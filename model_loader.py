# model_loader.py
import torch

def load_model(path="inefficient_model.pt", device="cuda" if torch.cuda.is_available() else "cpu"):
    """
    Load the pre-trained PyTorch model from file.
    This is done once at startup for efficiency.
    """
    model = torch.load(path, map_location=torch.device(device))
    model.eval()  # set model to evaluation mode
    return model
