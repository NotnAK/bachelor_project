import React, { useState } from "react";

function App() {
  const [image, setImage] = useState(null);
  const [prompt, setPrompt] = useState("<CAPTION>"); // По умолчанию описание
  const [results, setResults] = useState([]); // Теперь храним массив ответов

  const handleFileChange = (e) => {
    setImage(e.target.files[0]);
    console.log("Выбрано изображение:", e.target.files[0]);
  };

  const handlePromptChange = (e) => {
    setPrompt(e.target.value);
    console.log("Выбран prompt:", e.target.value);
  };

  const handleSubmit = async () => {
    if (!image || !prompt) {
      alert("Please select an image and enter a prompt!");
      console.warn("Попытка отправки без изображения или промпта!");
      return;
    }

    const formData = new FormData();
    formData.append("image", image);
    formData.append("prompt", prompt);

    console.log("Отправляем запрос на сервер:");
    console.log("Изображение:", image.name);
    console.log("Prompt:", prompt);

    try {
      const response = await fetch("http://127.0.0.1:8000/api/florence/", {
        method: "POST",
        body: formData,
      });

      console.log("Статус ответа:", response.status);

      if (!response.ok) {
        throw new Error(`Ошибка HTTP: ${response.status}`);
      }

      const data = await response.json();
      console.log("Ответ от сервера:", data);

      if (Array.isArray(data.result)) {
        setResults(data.result); // Если массив, записываем его в состояние
      } else {
        setResults([{ text: "No result" }]); // Если пусто, записываем заглушку
      }
    } catch (err) {
      console.error("Ошибка при отправке запроса:", err);
      setResults([{ text: "Error occurred!" }]);
    }
  };

  return (
    <div style={{ maxWidth: "600px", margin: "0 auto", padding: "1rem" }}>
      <h1>Florence-2 Inference</h1>

      <div style={{ marginBottom: "1rem" }}>
        <label>Upload Image:</label>
        <input type="file" accept="image/*" onChange={handleFileChange} />
      </div>

      <div style={{ marginBottom: "1rem" }}>
        <label>Prompt (Select Task):</label>
        <select value={prompt} onChange={handlePromptChange}>
          <option value="<CAPTION>">Caption</option>
          <option value="<MORE_DETAILED_CAPTION>">More Detailed Caption</option>
          <option value="<OD>">Object Detection</option>
          <option value="<OCR>">Text Recognition (OCR)</option>
        </select>
      </div>

      <button onClick={handleSubmit}>Run</button>

      <div style={{ marginTop: "1rem" }}>
        <h3>Result:</h3>
        <ul>
          {results.map((res, index) => (
            <li key={index}>{res.text}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

export default App;
