import React from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

function App() {
  return <main><header><div><strong>ГИП</strong><span>Инженер-обследователь</span></div><div className="status">Фундамент системы</div></header><section className="hero"><p className="eyebrow">ENGINEER OS</p><h1>Проверка инженерных отчётов</h1><p>Документы, расчёты и графика будут проверяться раздельно, а затем сопоставляться.</p><div className="cards"><article><b>01</b><h2>Основной отчёт</h2><p>DOCX / PDF / фотографии</p></article><article><b>02</b><h2>Расчёты</h2><p>DOC / DOCX / XLSX</p></article><article><b>03</b><h2>Сверка</h2><p>Контекстная проверка без ложных ошибок</p></article></div></section></main>;
}
createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
