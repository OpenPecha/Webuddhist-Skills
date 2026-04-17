from model import get_model_router


model_router = get_model_router()
model = model_router.get_model("gemini-2.5-flash")