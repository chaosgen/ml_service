# model_loader.py
import torch
from utils.create_model import InefficientModel

def load_model(path="model/inefficient_model.pt", device="cuda" if torch.cuda.is_available() else "cpu"):
    """
    Load the pre-trained PyTorch model from file.
    This is done once at startup for efficiency.
    """
    model = InefficientModel(in_dim=3)
    state_dict = torch.load(path, map_location=torch.device(device))
    model.load_state_dict(state_dict)
    model.to(device)
    model.eval()
    return model

if __name__ == "__main__":
    model = load_model()
    print(f"Model output {model(torch.randn(1, 3).to('cuda'))}")
    print("Model loaded successfully.")
