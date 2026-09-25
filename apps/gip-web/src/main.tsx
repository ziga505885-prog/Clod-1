import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./styles.css";

type Result = { findings: Array<{ code?: string; message?: string; severity?: string }>; traces: Array<Record<string, unknown>>; sources: string[] };

function App() {
  const [files, setFiles] = useState<File[]>([]);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function fullCheckAndFix() {
    if (!files.length) return;
    setLoading(true); setError(""); setResult(null);
    const form = new FormData();
    form.append("report", files[0]);
    try {
      const r = await fetch("http://localhost:8000/api/v1/full-check-and-fix", { method: "POST", body: form });
      if (!r.ok) throw new Error(await r.text());
      const blob = await r.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = "GIP_CORRECTED_" + files[0].name; a.click();
      URL.revokeObjectURL(url);
      setResult({findings: [], traces: [], sources: ["Исправленный DOCX сформирован"]});
    } catch (e) { setError(e instanceof Error ? e.message : "Ошибка исправления"); }
    finally { setLoading(false); }
  }

  async function fullCheck() {
    if (!files.length) return;
    setLoading(true); setError(""); setResult(null);
    const form = new FormData();
    form.append("report", files[0]);
    files.slice(1).forEach(f => form.append("calculation_files", f));
    try {
      const r = await fetch("http://localhost:8000/api/v1/full-check", { method: "POST", body: form });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e) { setError(e instanceof Error ? e.message : "Ошибка соединения с API"); }
    finally { setLoading(false); }
  }

  async function analyzeReport() {
    if (!files.length) return;
    setLoading(true); setError(""); setResult(null);
    const form = new FormData();
    form.append("file", files[0]);
    try {
      const r = await fetch("http://localhost:8000/api/v1/reports/analyze", { method: "POST", body: form });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e) { setError(e instanceof Error ? e.message : "Ошибка соединения с API"); }
    finally { setLoading(false); }
  }

  async function analyze() {
    if (!files.length) return;
    setLoading(true); setError(""); setResult(null);
    const form = new FormData();
    files.forEach(f => form.append("files", f));
    try {
      const r = await fetch("http://localhost:8000/api/v1/calculations/analyze", { method: "POST", body: form });
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
    } catch (e) { setError(e instanceof Error ? e.message : "Ошибка соединения с API"); }
    finally { setLoading(false); }
  }

  return <main>
    <header><div><strong>ГИП</strong><span>Инженер-обследователь</span></div><div className="status">Фундамент системы</div></header>
    <section className="hero">
      <p className="eyebrow">ENGINEER OS</p>
      <h1>Проверка инженерных расчётов</h1>
      <p>Загрузи расчётные материалы. ГИП анализирует их отдельно, сохраняя исходные значения.</p>
      <label className="upload"><input type="file" multiple accept=".doc,.docx,.xlsx" onChange={e => setFiles(Array.from(e.target.files ?? []))}/><b>Выбрать расчётные файлы</b><span>{files.length ? files.map(f => f.name).join(", ") : "DOC / DOCX / XLSX"}</span></label>
      <div className="actions"><button disabled={!files.length || loading} onClick={analyzeReport}>Проверить отчёт</button><button disabled={!files.length || loading} onClick={fullCheck}>Полная проверка</button><button disabled={!files.length || loading} onClick={fullCheckAndFix}>Проверить и исправить DOCX</button><button disabled={!files.length || loading} onClick={analyze}>{loading ? "Проверяем…" : "Проверить расчёты"}</button></div>
      {error && <div className="error">{error}</div>}
      {result && <section className="result"><h2>Результат проверки</h2><p>Файлы: {result.sources.join(", ")}</p><h3>Замечания</h3>{result.findings.length ? result.findings.map((f,i)=><article key={i}><b>{f.code ?? "FINDING"}</b><p>{f.message ?? JSON.stringify(f)}</p></article>) : <p>Детерминированных замечаний не обнаружено.</p>}<h3>Расчётный контекст</h3><p>{result.traces.length} контекстных фрагментов извлечено.</p></section>}
    </section>
  </main>;
}
createRoot(document.getElementById("root")!).render(<React.StrictMode><App /></React.StrictMode>);
