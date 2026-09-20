import { useEffect, useRef, useState } from "react";

const API_BASE = "https://healthcare-ai-platform-qr5x.onrender.com";
const PATIENT_ID = 3;
const SESSION_ID = "patient-3";

export default function VoiceAssistant({ onClose }) {
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [status, setStatus] = useState("Ready");
  const [transcript, setTranscript] = useState("");
  const [response, setResponse] = useState("");

  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setStatus("Voice recognition is not supported in this browser.");
      return;
    }

    const recognition = new SpeechRecognition();

    recognition.lang = "en-IN";
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      setListening(true);
      setStatus("Listening...");
    };

    recognition.onresult = async (event) => {
      const text = event.results[0][0].transcript;

      setTranscript(text);
      setListening(false);
      setStatus("Processing...");

      await sendToAI(text);
    };

    recognition.onerror = (event) => {
      setListening(false);
      setStatus(`Voice error: ${event.error}`);
    };

    recognition.onend = () => {
      setListening(false);
    };

    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
    };
  }, []);

  async function sendToAI(message) {
    try {
      const result = await fetch(`${API_BASE}/ai/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          patient_id: PATIENT_ID,
          session_id: SESSION_ID,
          message,
        }),
      });

      if (!result.ok) {
        throw new Error("AI request failed");
      }

      const data = await result.json();

      const aiMessage =
        data.message ||
        data.response ||
        data.capability_result?.message ||
        "I could not process that request.";

      setResponse(aiMessage);
      setStatus("Speaking...");

      speak(aiMessage);
    } catch (error) {
      console.error(error);
      setStatus("Unable to connect to the AI service.");
    }
  }

  function startListening() {
    if (!recognitionRef.current) {
      setStatus("Speech recognition is unavailable.");
      return;
    }

    setTranscript("");
    setResponse("");

    try {
      recognitionRef.current.start();
    } catch (error) {
      console.error(error);
    }
  }

  function speak(text) {
    if (!window.speechSynthesis) {
      setStatus("Text-to-speech is not supported.");
      return;
    }

    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);

    utterance.lang = "en-IN";
    utterance.rate = 1;
    utterance.pitch = 1;

    utterance.onstart = () => {
      setSpeaking(true);
    };

    utterance.onend = () => {
      setSpeaking(false);
      setStatus("Ready");
    };

    utterance.onerror = () => {
      setSpeaking(false);
      setStatus("Speech output failed.");
    };

    window.speechSynthesis.speak(utterance);
  }

  return (
    <div className="voice-overlay">
      <div className="voice-card">
        <div className="voice-header">
          <div>
            <h2>Healthcare Voice Assistant</h2>
            <p>Speak naturally to book or manage your appointment.</p>
          </div>

          <button
            className="voice-close"
            onClick={onClose}
          >
            ×
          </button>
        </div>

        <div className="voice-status">
          <div
            className={`voice-circle ${
              listening ? "listening" : ""
            } ${speaking ? "speaking" : ""}`}
          >
            🎙️
          </div>

          <strong>{status}</strong>
        </div>

        {transcript && (
          <div className="voice-message">
            <span>You said</span>
            <p>{transcript}</p>
          </div>
        )}

        {response && (
          <div className="voice-message assistant">
            <span>Assistant</span>
            <p>{response}</p>
          </div>
        )}

        <button
          className="voice-button"
          onClick={startListening}
          disabled={listening || speaking}
        >
          {listening ? "Listening..." : "🎤 Speak"}
        </button>

        <p className="voice-hint">
          Example: “I need an orthopedic doctor”
        </p>
      </div>
    </div>
  );
}
