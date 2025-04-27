# text_embedding.py
import torch
import numpy as np
from transformers import AutoModelForCausalLM, BartTokenizerFast

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Желаемая размерность общего пространства (например, 1024)
DESIRED_DIM = 1024


def generate_text_embedding(text: str) -> np.ndarray:
    # Загружаем модель Florence‑2 (языковая часть)
    model = AutoModelForCausalLM.from_pretrained(
        "microsoft/Florence-2-base-ft",
        trust_remote_code=True,
        revision="refs/pr/6"
    ).to(DEVICE)

    # Загружаем токенизатор (на базе BartTokenizerFast)
    tokenizer = BartTokenizerFast.from_pretrained(
        "microsoft/Florence-2-base-ft",
        trust_remote_code=True,
        revision="refs/pr/6"
    )

    model.eval()

    # Токенизируем входной текст
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(DEVICE)

    with torch.no_grad():
        # Получаем скрытые состояния энкодера (форма: [batch_size, seq_len, d_model])
        encoder_outputs = model.get_encoder()(
            input_ids=inputs.input_ids,
            attention_mask=inputs.attention_mask,
            output_hidden_states=True
        )
        # Усредняем по токенам, получая вектор [batch_size, d_model]
        text_emb = encoder_outputs.last_hidden_state.mean(dim=1)

    current_dim = text_emb.shape[-1]
    # Если размерность не совпадает с желаемой, применяем проекцию
    if current_dim != DESIRED_DIM:
        projection = torch.nn.Linear(current_dim, DESIRED_DIM).to(DEVICE)
        # Если нужно, можно инициализировать веса projection по схеме из документации
        torch.nn.init.normal_(projection.weight, std=0.02)
        torch.nn.init.constant_(projection.bias, 0)
        text_emb = projection(text_emb)

    # L2-нормализация
    text_emb = text_emb / torch.norm(text_emb, p=2, dim=-1, keepdim=True)

    # Сжимаем размерность batch, если batch_size == 1
    return text_emb.squeeze(0).detach().cpu().numpy()


if __name__ == "__main__":
    np.set_printoptions(threshold=np.inf)
    print("Введите текст для генерации эмбеддинга (или 'exit' для выхода):")
    while True:
        user_input = input(">> ")
        if user_input.strip().lower() == "exit":
            break
        emb = generate_text_embedding(user_input)
        print("Эмбеддинг ({}-dim):".format(emb.shape[0]))
        print(emb)
        print("Размер эмбеддинга:", emb.shape)
