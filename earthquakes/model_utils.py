import torch
import torch.nn as nn
import pickle
import numpy as np
import os
from pathlib import Path

class EarthquakeModel(nn.Module):
    def __init__(self, input_size=22):
        super(EarthquakeModel, self).__init__()
        self.linear1 = nn.Linear(input_size, 128)
        self.bn1 = nn.BatchNorm1d(128)
        self.relu1 = nn.ReLU()
        self.linear2 = nn.Linear(128, 64)
        self.bn2 = nn.BatchNorm1d(64)
        self.relu2 = nn.ReLU()
        self.linear3 = nn.Linear(64, 32)
        self.bn3 = nn.BatchNorm1d(32)
        self.relu3 = nn.ReLU()
        self.linear4 = nn.Linear(32, 1)
        self.sigmoid = nn.Sigmoid()
    
    def forward(self, x):
        x = self.linear1(x)
        x = self.bn1(x)
        x = self.relu1(x)
        x = self.linear2(x)
        x = self.bn2(x)
        x = self.relu2(x)
        x = self.linear3(x)
        x = self.bn3(x)
        x = self.relu3(x)
        x = self.linear4(x)
        x = self.sigmoid(x)
        return x

class EarthquakePredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.load_model()
    
    def load_model(self):
        """Load the trained PyTorch model and scaler"""
        try:
            # Get the directory containing this file
            current_dir = Path(__file__).parent
            model_path = current_dir / 'models' / 'earthquake_model.pt'
            scaler_path = current_dir / 'models' / 'earthquake_scaler.pkl'
            
            # Create model instance
            self.model = EarthquakeModel()
            
            # Load the state dictionary
            state_dict = torch.load(model_path, map_location=self.device)
            
            # Create mapping for layer indices to names
            layer_mapping = {
                '0': 'linear1',
                '2': 'bn1',
                '4': 'linear2',
                '6': 'bn2',
                '8': 'linear3',
                '10': 'bn3',
                '12': 'linear4'
            }
            
            # Rename the keys to match our model's structure
            new_state_dict = {}
            for k, v in state_dict.items():
                # Get the layer index (before the first dot)
                layer_idx = k.split('.')[0]
                if layer_idx in layer_mapping:
                    # Get the layer name
                    layer_name = layer_mapping[layer_idx]
                    # Get the parameter name (after the first dot)
                    param_name = k[k.find('.')+1:]
                    # Create the new key
                    new_key = f"{layer_name}.{param_name}"
                    new_state_dict[new_key] = v
            
            self.model.load_state_dict(new_state_dict)
            
            # Set to evaluation mode
            self.model.eval()
            
            # Load the scaler
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
                
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            raise
    
    def preprocess_data(self, features):
        """Preprocess input features using the loaded scaler"""
        if self.scaler is None:
            raise ValueError("Scaler not loaded")
        
        # Ensure we have all 22 features
        if len(features) < 22:
            # Pad with zeros if we don't have all features
            features = np.pad(features, (0, 22 - len(features)), 'constant')
        
        # Convert features to numpy array and reshape if needed
        features = np.array(features).reshape(1, -1)
        
        # Scale the features
        scaled_features = self.scaler.transform(features)
        
        # Convert to PyTorch tensor
        return torch.FloatTensor(scaled_features).to(self.device)
    
    def predict(self, features):
        """Make predictions using the loaded model"""
        if self.model is None:
            raise ValueError("Model not loaded")
        
        try:
            # Preprocess the input features
            input_tensor = self.preprocess_data(features)
            
            # Make prediction
            with torch.no_grad():
                prediction = self.model(input_tensor)
            
            # Convert prediction to numpy array
            prediction = prediction.cpu().numpy()
            
            return prediction[0]
            
        except Exception as e:
            print(f"Error making prediction: {str(e)}")
            raise

# Create a global instance of the predictor
predictor = None

def get_predictor():
    """Get or create the earthquake predictor instance"""
    global predictor
    if predictor is None:
        predictor = EarthquakePredictor()
    return predictor

def predict_earthquake_risk(features):
    """Predict earthquake risk using the trained model"""
    try:
        predictor = get_predictor()
        prediction = predictor.predict(features)
        
        # Convert prediction to risk level (0-3)
        risk_level = int(prediction[0] * 3)  # Scale prediction to 0-3 range
        
        # Generate risk details based on prediction
        if risk_level == 0:
            details = "No immediate earthquake risk predicted."
        elif risk_level == 1:
            details = "Low earthquake risk predicted. Stay alert."
        elif risk_level == 2:
            details = "Moderate earthquake risk predicted. Prepare for potential evacuation."
        else:
            details = "High earthquake risk predicted. Immediate action required."
        
        return {
            'risk_level': risk_level,
            'details': details,
            'raw_prediction': float(prediction[0])
        }
        
    except Exception as e:
        print(f"Error in earthquake prediction: {str(e)}")
        return {
            'risk_level': 0,
            'details': "Unable to make prediction due to error",
            'raw_prediction': 0.0
        } 