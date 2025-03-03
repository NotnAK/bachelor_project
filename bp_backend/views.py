import logging
from inference import get_model
from rest_framework.decorators import api_view
from rest_framework.response import Response
from PIL import Image

# === Настраиваем логирование ===
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# === API-ключ Roboflow (замени на свой) ===
ROBOFLOW_API_KEY = "tapBxwMwkvdW9Of35nNz"

# === Инициализируем модель Florence-2 ===
logger.info("Initializing Florence-2 model with Roboflow API key...")
model = get_model("florence-2-base", api_key=ROBOFLOW_API_KEY)

@api_view(["POST"])
def florence_inference(request):
    """
    Принимает изображение и prompt, отправляет их в Florence-2 через Roboflow.
    Возвращает результат в формате JSON.
    """
    logger.info("Received request at /api/florence/")

    # Проверяем, есть ли изображение и prompt
    image_file = request.FILES.get('image')
    prompt = request.data.get('prompt', '')

    if not image_file:
        logger.error("No image provided in the request!")
        return Response({"error": "No image provided"}, status=400)

    logger.info(f"Received image: {image_file.name}, size: {image_file.size} bytes")
    logger.info(f"Received prompt: {prompt}")

    # Открываем изображение и конвертируем в RGB
    try:
        image = Image.open(image_file).convert("RGB")
    except Exception as e:
        logger.error(f"Error opening image: {str(e)}")
        return Response({"error": "Invalid image format"}, status=400)

    # Отправляем изображение и prompt в Florence-2 через Roboflow
    try:
        logger.info("Sending image and prompt to Florence-2...")
        result = model.infer(image, prompt=prompt)  # Используем `prompt`

        if not result:
            return Response({"result": "No response from Florence-2"})

        response_data = []
        for res in result:
            # Florence-2 может возвращать объект { "<CAPTION>": "Text" }, конвертируем его в текст
            if isinstance(res.response, dict):
                parsed_text = " | ".join(res.response.values())  # Объединяем все строки через `|`
            else:
                parsed_text = str(res.response)  # Обычная строка

            response_data.append({"text": parsed_text})

        logger.info(f"Response from Florence-2: {response_data}")
        return Response({"result": response_data})  # Отправляем массив JSON
    except Exception as e:
        logger.error(f"Error processing request with Florence-2: {str(e)}")
        return Response({"error": str(e)}, status=500)
