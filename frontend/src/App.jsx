import { useState } from "react";
import DoctorDashboard from "./DoctorDashboard.jsx";
import AdminDashboard from "./AdminDashboard.jsx";
import VoiceAssistant from "./VoiceAssistant.jsx";
import "./index.css";

const API_BASE = "https://healthcare-ai-platform-qr5x.onrender.com";
const PATIENT_ID = 1;
const SESSION_ID = "patient-3";

// Prototype appointment used when questionnaire is opened
// after the currently tested booking.
const DEFAULT_APPOINTMENT_ID = null;

function formatSlotTime(value) {
  if (!value) return "";

  const date = new Date(value);

  return date.toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

function formatTimeOnly(value) {
  if (!value) return "";

  const date = new Date(value);

  return date.toLocaleTimeString("en-IN", {
    hour: "numeric",
    minute: "2-digit",
    hour12: true,
  });
}

const APP_STYLES = `
  * {
    box-sizing: border-box;
  }

  body {
    margin: 0;
    font-family:
      Inter,
      system-ui,
      -apple-system,
      BlinkMacSystemFont,
      "Segoe UI",
      sans-serif;
    background: #f5f8fc;
    color: #172033;
  }

  button,
  input,
  textarea,
  select {
    font: inherit;
  }

  button {
    cursor: pointer;
  }

  .app-shell {
    min-height: 100vh;
    background:
      radial-gradient(circle at top right, #e9f2ff 0, transparent 30%),
      #f5f8fc;
  }

  .topbar {
    height: 76px;
    padding: 0 5%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    background: rgba(255, 255, 255, 0.96);
    border-bottom: 1px solid #e3eaf4;
    position: sticky;
    top: 0;
    z-index: 50;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .brand-icon {
    width: 42px;
    height: 42px;
    border-radius: 12px;
    display: grid;
    place-items: center;
    background: #eaf2ff;
    font-size: 22px;
  }

  .brand-title {
    font-size: 20px;
    font-weight: 800;
  }

  .brand-subtitle {
    font-size: 12px;
    color: #718096;
  }

  .nav-actions {
    display: flex;
    gap: 8px;
  }

  .nav-button {
    border: 1px solid #dbe4f0;
    background: white;
    color: #344054;
    border-radius: 10px;
    padding: 10px 14px;
    font-weight: 700;
  }

  .nav-button:hover {
    background: #f3f7fd;
  }

  .nav-button.active {
    background: #eef5ff;
    color: #245ec7;
    border-color: #b9d2ff;
  }

  .hero {
    max-width: 1050px;
    margin: 0 auto;
    padding: 65px 20px 35px;
    text-align: center;
  }

  .hero-badge {
    display: inline-block;
    padding: 8px 14px;
    border-radius: 30px;
    background: #eaf3ff;
    color: #2563c9;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 18px;
  }

  .hero h1 {
    margin: 0;
    font-size: clamp(38px, 6vw, 64px);
    line-height: 1.05;
    letter-spacing: -2px;
  }

  .hero h1 span {
    color: #3778db;
  }

  .hero p {
    max-width: 700px;
    margin: 20px auto;
    color: #667085;
    line-height: 1.7;
  }

  .voice-launch {
    border: none;
    background: #3778db;
    color: white;
    border-radius: 14px;
    padding: 14px 22px;
    font-weight: 800;
    box-shadow: 0 10px 25px rgba(55, 120, 219, 0.2);
  }

  .voice-launch:hover {
    transform: translateY(-1px);
  }

  .main-content {
    max-width: 1050px;
    margin: 0 auto;
    padding: 0 20px 60px;
  }

  .chat-card {
    background: white;
    border: 1px solid #e0e8f3;
    border-radius: 22px;
    overflow: hidden;
    box-shadow: 0 12px 35px rgba(31, 53, 86, 0.07);
  }

  .chat-header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 20px 22px;
    border-bottom: 1px solid #edf1f7;
  }

  .assistant-avatar {
    width: 44px;
    height: 44px;
    display: grid;
    place-items: center;
    background: #eef5ff;
    border-radius: 14px;
    font-size: 23px;
  }

  .chat-header h2 {
    margin: 0;
    font-size: 18px;
  }

  .chat-header p {
    margin: 4px 0 0;
    color: #7a8699;
    font-size: 13px;
  }

  .clear-button {
    margin-left: auto;
    border: 1px solid #e1e7ef;
    background: white;
    border-radius: 8px;
    padding: 8px 12px;
    color: #667085;
  }

  .messages {
    min-height: 220px;
    max-height: 460px;
    overflow-y: auto;
    padding: 22px;
  }

  .message-row {
    display: flex;
    gap: 9px;
    margin-bottom: 13px;
  }

  .assistant-row {
    justify-content: flex-start;
  }

  .user-row {
    justify-content: flex-end;
  }

  .small-avatar {
    width: 30px;
    height: 30px;
    display: grid;
    place-items: center;
    border-radius: 10px;
    background: #eef5ff;
    flex-shrink: 0;
  }

  .message-bubble {
    max-width: 78%;
    padding: 12px 15px;
    border-radius: 14px;
    line-height: 1.5;
    font-size: 14px;
  }

  .assistant-bubble {
    background: #f1f6fc;
    color: #27364d;
  }

  .user-bubble {
    background: #3778db;
    color: white;
  }

  .typing {
    display: flex;
    gap: 4px;
  }

  .slots-section {
    padding: 20px 22px;
    border-top: 1px solid #edf1f7;
  }

  .section-title {
    font-weight: 800;
    margin-bottom: 13px;
  }

  .slot-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 10px;
  }

  .slot-card {
    text-align: left;
    border: 1px solid #d9e5f5;
    background: #f8fbff;
    border-radius: 13px;
    padding: 14px;
    color: #24344d;
  }

  .slot-card:hover {
    border-color: #6f9fe5;
    background: #eef5ff;
  }

  .slot-card:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .slot-card strong,
  .slot-card span,
  .slot-card small {
    display: block;
  }

  .slot-card span {
    margin-top: 5px;
    color: #63728a;
    font-size: 12px;
  }

  .slot-card small {
    margin-top: 10px;
    color: #3778db;
    font-weight: 700;
  }

  .success-card {
    margin: 0 22px 18px;
    padding: 17px;
    border-radius: 14px;
    background: #edfdf4;
    border: 1px solid #bde8ce;
    display: flex;
    gap: 13px;
  }

  .success-icon {
    width: 34px;
    height: 34px;
    border-radius: 50%;
    background: #25a35a;
    color: white;
    display: grid;
    place-items: center;
    font-weight: 900;
  }

  .success-card h3 {
    margin: 0 0 6px;
  }

  .success-card p {
    margin: 5px 0;
    color: #46604f;
    font-size: 14px;
  }

  .error-card {
    margin: 0 22px 18px;
    padding: 13px;
    border-radius: 10px;
    background: #fff1f1;
    border: 1px solid #ffcaca;
    color: #a13232;
  }

  .quick-section {
    padding: 17px 22px;
    border-top: 1px solid #edf1f7;
  }

  .quick-section > span {
    display: block;
    color: #7b8798;
    font-size: 13px;
    font-weight: 700;
    margin-bottom: 10px;
  }

  .quick-actions {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .quick-actions button {
    border: 1px solid #d7e1ee;
    background: white;
    color: #344054;
    border-radius: 9px;
    padding: 9px 13px;
    font-weight: 600;
  }

  .quick-actions button:hover {
    background: #f4f8fd;
    border-color: #b9cce6;
  }

  .input-area {
    padding: 15px 20px 22px;
    display: flex;
    gap: 8px;
  }

  .input-area input {
    flex: 1;
    min-width: 0;
    border: 1px solid #d9e2ef;
    border-radius: 12px;
    padding: 14px;
    outline: none;
  }

  .input-area input:focus {
    border-color: #6e9de1;
  }

  .send-button {
    border: none;
    background: #3778db;
    color: white;
    border-radius: 12px;
    padding: 0 20px;
    font-weight: 800;
  }

  .send-button:disabled {
    opacity: 0.55;
  }

  .features {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-top: 22px;
  }

  .feature-card {
    background: white;
    border: 1px solid #e0e8f3;
    border-radius: 15px;
    padding: 20px;
  }

  .feature-icon {
    font-size: 25px;
    margin-bottom: 12px;
  }

  .feature-card h3 {
    margin: 0 0 8px;
    font-size: 15px;
  }

  .feature-card p {
    margin: 0;
    color: #738095;
    font-size: 13px;
    line-height: 1.5;
  }

  .footer {
    text-align: center;
    padding: 25px;
    color: #748197;
    font-size: 12px;
  }

  .dashboard-header {
    padding: 25px 5%;
    background: white;
    border-bottom: 1px solid #e3eaf4;
  }

  .dashboard-header h1 {
    margin: 14px 0 4px;
  }

  .dashboard-header p {
    margin: 0;
    color: #718096;
  }

  .back-button {
    border: 1px solid #dbe4f0;
    background: white;
    border-radius: 9px;
    padding: 9px 13px;
  }

  .questionnaire-overlay {
    position: fixed;
    inset: 0;
    z-index: 1000;
    background: rgba(15, 23, 42, 0.58);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 20px;
  }

  .questionnaire-card {
    width: 100%;
    max-width: 680px;
    max-height: 90vh;
    overflow-y: auto;
    background: white;
    border-radius: 22px;
    padding: 28px;
    box-shadow: 0 25px 70px rgba(0, 0, 0, 0.22);
  }

  .questionnaire-header {
    display: flex;
    justify-content: space-between;
    gap: 15px;
    align-items: flex-start;
    margin-bottom: 22px;
  }

  .questionnaire-header h2 {
    margin: 0 0 7px;
  }

  .questionnaire-header p {
    margin: 0;
    color: #718096;
    line-height: 1.5;
    font-size: 14px;
  }

  .questionnaire-close {
    border: none;
    background: #f1f5f9;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    font-size: 20px;
    flex-shrink: 0;
  }

  .question-group {
    margin-bottom: 20px;
  }

  .question-group label {
    display: block;
    font-weight: 700;
    margin-bottom: 8px;
    line-height: 1.5;
  }

  .question-group input,
  .question-group select,
  .question-group textarea {
    width: 100%;
    border: 1px solid #d4deeb;
    border-radius: 10px;
    padding: 12px;
    outline: none;
    background: white;
  }

  .question-group input:focus,
  .question-group select:focus,
  .question-group textarea:focus {
    border-color: #3778db;
  }

  .question-group textarea {
    resize: vertical;
  }

  .questionnaire-message {
    padding: 12px 14px;
    border-radius: 10px;
    background: #eef6ff;
    color: #285b9e;
    margin-bottom: 16px;
    line-height: 1.5;
  }

  .questionnaire-submit {
    width: 100%;
    border: none;
    border-radius: 11px;
    padding: 14px;
    background: #3778db;
    color: white;
    font-weight: 800;
  }

  .questionnaire-submit:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  @media (max-width: 800px) {
    .topbar {
      height: auto;
      padding: 14px 20px;
      align-items: flex-start;
      flex-direction: column;
    }

    .nav-actions {
      width: 100%;
      overflow-x: auto;
    }

    .features {
      grid-template-columns: 1fr 1fr;
    }
  }

  @media (max-width: 550px) {
    .hero {
      padding-top: 40px;
    }

    .hero h1 {
      font-size: 40px;
    }

    .features {
      grid-template-columns: 1fr;
    }

    .input-area {
      flex-direction: column;
    }

    .send-button {
      padding: 12px;
    }
  }
`;

function App() {
  const [view, setView] = useState("patient");

  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hello! 👋 I’m your healthcare assistant. I can help you find an orthopedic doctor, check real appointment availability, and book an appointment.",
    },
  ]);

  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [slots, setSlots] = useState([]);
  const [booking, setBooking] = useState(false);
  const [bookingSuccess, setBookingSuccess] = useState(null);
  const [error, setError] = useState("");
  const [showVoice, setShowVoice] = useState(false);

  // Questionnaire state
  const [showQuestionnaire, setShowQuestionnaire] = useState(false);
  const [questionnaireLoading, setQuestionnaireLoading] = useState(false);
  const [questionnaireMessage, setQuestionnaireMessage] = useState("");
  const [questionnaireAppointmentId, setQuestionnaireAppointmentId] =
    useState(DEFAULT_APPOINTMENT_ID);

  const [questionnaireAnswers, setQuestionnaireAnswers] = useState({
    1: "",
    2: "",
    3: "",
    4: "",
  });

  async function sendMessage(message) {
    const cleanMessage = message.trim();

    if (!cleanMessage || loading) {
      return null;
    }

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: cleanMessage,
      },
    ]);

    setInput("");
    setLoading(true);
    setError("");
    setBookingSuccess(null);

    try {
      const response = await fetch(`${API_BASE}/ai/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          patient_id: PATIENT_ID,
          session_id: SESSION_ID,
          message: cleanMessage,
        }),
      });

      if (!response.ok) {
        let detail = `AI request failed (${response.status})`;

        try {
          const errorData = await response.json();
          detail = errorData.detail || detail;
        } catch {
          // Keep default error.
        }

        throw new Error(detail);
      }

      const data = await response.json();

      const capabilityResult =
        data?.capability_result &&
        typeof data.capability_result === "object"
          ? data.capability_result
          : {};

      const assistantMessage =
        data?.message ||
        data?.response ||
        capabilityResult?.message ||
        "I processed your request.";

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: assistantMessage,
        },
      ]);

      const returnedSlots = Array.isArray(capabilityResult?.slots)
        ? capabilityResult.slots
        : [];

      if (returnedSlots.length > 0) {
        setSlots(returnedSlots);
      } else if (
        capabilityResult?.capability_result === "booking_confirmed" ||
        capabilityResult?.capability_result === "booking_recovered" ||
        (data?.success === true &&
          (data?.appointment_id || data?.external_appointment_id))
      ) {
        setSlots([]);
      }

      if (
        capabilityResult?.capability_result === "booking_confirmed" ||
        capabilityResult?.capability_result === "booking_recovered"
      ) {
        const appointmentId = data?.appointment_id;

        setBookingSuccess({
          message: assistantMessage,
          appointmentId,
          externalId: data?.external_appointment_id,
          recovery:
            capabilityResult?.capability_result === "booking_recovered",
        });

        if (appointmentId) {
          setQuestionnaireAppointmentId(appointmentId);
        }
      }

      return data;
    } catch (requestError) {
      console.error(requestError);

      setError(
        requestError?.message ||
          "Unable to connect to the healthcare AI service."
      );

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content:
            "Sorry, I could not connect to the healthcare service. Please check that the backend is running.",
        },
      ]);

      return null;
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!input.trim() || loading) {
      return;
    }

    await sendMessage(input);
  }

  async function handleQuickAction(message) {
    await sendMessage(message);
  }

  async function handleBookSlot(slot) {
    if (!slot?.start_time || booking || loading) {
      return;
    }

    setBooking(true);
    setError("");
    setBookingSuccess(null);

    const requestedTime = formatTimeOnly(slot.start_time);

    try {
      const result = await sendMessage(
        `Book the ${requestedTime} appointment`
      );

      if (
        result?.success === true ||
        result?.capability_result?.capability_result ===
          "booking_confirmed" ||
        result?.capability_result?.capability_result ===
          "booking_recovered"
      ) {
        setSlots([]);

        if (result?.appointment_id) {
          setQuestionnaireAppointmentId(result.appointment_id);
        }
      }
    } finally {
      setBooking(false);
    }
  }

  function clearConversation() {
    setMessages([
      {
        role: "assistant",
        content:
          "Hello! 👋 I’m your healthcare assistant. I can help you find an orthopedic doctor, check real appointment availability, and book an appointment.",
      },
    ]);

    setSlots([]);
    setBookingSuccess(null);
    setError("");
    setInput("");
  }

  function openQuestionnaire() {
    setQuestionnaireMessage("");
    setShowQuestionnaire(true);
  }

  function updateQuestionnaireAnswer(questionId, value) {
    setQuestionnaireAnswers((previous) => ({
      ...previous,
      [questionId]: value,
    }));
  }

  async function submitQuestionnaire() {
    const requiredQuestions = [1, 2, 3];

    const missingRequired = requiredQuestions.some(
      (questionId) => !questionnaireAnswers[questionId].trim()
    );

    if (missingRequired) {
      setQuestionnaireMessage(
        "Please answer all required questions before submitting."
      );
      return;
    }

    setQuestionnaireLoading(true);
    setQuestionnaireMessage("");

    try {
      const questionIds = [1, 2, 3, 4];

      for (const questionId of questionIds) {
        const answer = questionnaireAnswers[questionId].trim();

        if (!answer) {
          continue;
        }

        const response = await fetch(
          `${API_BASE}/questionnaire-responses/`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              id: 0,
              questionnaire_id: 1,
              question_id: questionId,
              appointment_id: questionnaireAppointmentId,
              patient_id: PATIENT_ID,
              answer,
            }),
          }
        );

        if (!response.ok) {
          let detail = "Failed to save questionnaire response.";

          try {
            const errorData = await response.json();
            detail = errorData.detail || detail;
          } catch {
            // Keep default error.
          }

          throw new Error(detail);
        }
      }

      setQuestionnaireMessage(
        "Questionnaire submitted successfully. Your doctor can review your responses."
      );
    } catch (requestError) {
      console.error(requestError);

      setQuestionnaireMessage(
        requestError?.message ||
          "Unable to submit the questionnaire. Please try again."
      );
    } finally {
      setQuestionnaireLoading(false);
    }
  }

  if (view === "doctor") {
    return (
      <div className="app-shell">
        <style>{APP_STYLES}</style>

        <div className="dashboard-header">
          <button
            className="back-button"
            onClick={() => setView("patient")}
          >
            ← Patient Assistant
          </button>

          <div>
            <h1>Doctor Dashboard</h1>
            <p>Appointments and patient questionnaire information</p>
          </div>
        </div>

        <DoctorDashboard />
      </div>
    );
  }

  if (view === "admin") {
    return (
      <div className="app-shell">
        <style>{APP_STYLES}</style>

        <div className="dashboard-header">
          <button
            className="back-button"
            onClick={() => setView("patient")}
          >
            ← Patient Assistant
          </button>

          <div>
            <h1>Admin Dashboard</h1>
            <p>Hospital operations, appointments and audit visibility</p>
          </div>
        </div>

        <AdminDashboard />
      </div>
    );
  }

  return (
    <div className="app-shell">
      <style>{APP_STYLES}</style>

      {/* TOP BAR */}
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">🏥</div>

          <div>
            <div className="brand-title">HealthAI</div>
            <div className="brand-subtitle">
              Healthcare Access Assistant
            </div>
          </div>
        </div>

        <div className="nav-actions">
          <button
            className="nav-button active"
            onClick={() => setView("patient")}
          >
            🤖 Patient Assistant
          </button>

          <button
            className="nav-button"
            onClick={() => setView("doctor")}
          >
            👨‍⚕️ Doctor Dashboard
          </button>

          <button
            className="nav-button"
            onClick={() => setView("admin")}
          >
            🏥 Admin Dashboard
          </button>
        </div>
      </header>

      {/* HERO */}
      <section className="hero">
        <div className="hero-badge">
          ✨ AI-powered healthcare assistance
        </div>

        <h1>
          Your healthcare appointment,
          <br />
          <span>made simpler.</span>
        </h1>

        <p>
          Find doctors, check real availability, and book appointments
          through a conversational healthcare assistant.
        </p>

        <button
          className="voice-launch"
          onClick={() => setShowVoice(true)}
        >
          🎙️ Talk to Healthcare Assistant
        </button>
      </section>

      {/* MAIN CHAT */}
      <main className="main-content">
        <section className="chat-card">
          <div className="chat-header">
            <div className="assistant-avatar">🤖</div>

            <div>
              <h2>Healthcare Assistant</h2>
              <p>Online • Administrative assistance only</p>
            </div>

            <button
              className="clear-button"
              onClick={clearConversation}
            >
              Clear
            </button>
          </div>

          {/* MESSAGES */}
          <div className="messages">
            {messages.map((message, index) => (
              <div
                key={`${message.role}-${index}`}
                className={`message-row ${
                  message.role === "user"
                    ? "user-row"
                    : "assistant-row"
                }`}
              >
                {message.role === "assistant" && (
                  <div className="small-avatar">🤖</div>
                )}

                <div
                  className={`message-bubble ${
                    message.role === "user"
                      ? "user-bubble"
                      : "assistant-bubble"
                  }`}
                >
                  {message.content}
                </div>
              </div>
            ))}

            {loading && (
              <div className="message-row assistant-row">
                <div className="small-avatar">🤖</div>

                <div className="message-bubble assistant-bubble typing">
                  <span>●</span>
                  <span>●</span>
                  <span>●</span>
                </div>
              </div>
            )}
          </div>

          {/* SLOTS */}
          {slots.length > 0 && (
            <div className="slots-section">
              <div className="section-title">
                📅 Available appointment slots
              </div>

              <div className="slot-grid">
                {slots.map((slot, index) => (
                  <button
                    key={`${slot.start_time}-${index}`}
                    className="slot-card"
                    onClick={() => handleBookSlot(slot)}
                    disabled={booking || loading}
                  >
                    <strong>
                      {formatSlotTime(slot.start_time)}
                    </strong>

                    <span>
                      {slot.appointment_type || "IN_PERSON"}
                    </span>

                    <small>
                      {booking
                        ? "Booking..."
                        : "Click to book →"}
                    </small>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* BOOKING SUCCESS */}
          {bookingSuccess && (
            <div className="success-card">
              <div className="success-icon">✓</div>

              <div>
                <h3>
                  {bookingSuccess.recovery
                    ? "Appointment recovered successfully"
                    : "Appointment confirmed"}
                </h3>

                <p>{bookingSuccess.message}</p>

                {bookingSuccess.appointmentId && (
                  <p>
                    <strong>Appointment ID:</strong>{" "}
                    {bookingSuccess.appointmentId}
                  </p>
                )}

                {bookingSuccess.externalId && (
                  <p>
                    <strong>External EHR ID:</strong>{" "}
                    {bookingSuccess.externalId}
                  </p>
                )}

                {/* Questionnaire after booking */}
                <button
                  className="quick-actions"
                  onClick={openQuestionnaire}
                  style={{
                    marginTop: "12px",
                    border: "1px solid #b9d2ff",
                    background: "#eef5ff",
                    color: "#245ec7",
                    borderRadius: "9px",
                    padding: "9px 13px",
                    fontWeight: "700",
                  }}
                >
                  📝 Complete Pre-Visit Questionnaire
                </button>
              </div>
            </div>
          )}

          {/* ERROR */}
          {error && (
            <div className="error-card">
              ⚠️ {error}
            </div>
          )}

          {/* QUICK ACTIONS */}
          <div className="quick-section">
            <span>Quick actions</span>

            <div className="quick-actions">
              <button onClick={openQuestionnaire}>
                📝 Pre-Visit Questionnaire
              </button>

              <button
                onClick={() =>
                  handleQuickAction(
                    "I need an orthopedic doctor"
                  )
                }
              >
                🦴 Find orthopedic doctor
              </button>

              <button
                onClick={() =>
                  handleQuickAction(
                    "Show available appointments"
                  )
                }
              >
                📅 Show available appointments
              </button>

              <button
                onClick={() =>
                  handleQuickAction(
                    "I want to book an appointment"
                  )
                }
              >
                🗓️ Book an appointment
              </button>
            </div>
          </div>

          {/* INPUT */}
          <form
            className="input-area"
            onSubmit={handleSubmit}
          >
            <input
              value={input}
              onChange={(event) =>
                setInput(event.target.value)
              }
              placeholder="Tell me what you need..."
              disabled={loading}
            />

            <button
              type="button"
              className="voice-launch"
              style={{
                padding: "0 18px",
                borderRadius: "12px",
              }}
              onClick={() => setShowVoice(true)}
            >
              🎤
            </button>

            <button
              type="submit"
              className="send-button"
              disabled={loading || !input.trim()}
            >
              Send
            </button>
          </form>
        </section>

        {/* FEATURES */}
        <section className="features">
          <div className="feature-card">
            <div className="feature-icon">🔎</div>
            <h3>Doctor Discovery</h3>
            <p>
              Find available doctors based on your appointment
              requirements.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">📅</div>
            <h3>Real Availability</h3>
            <p>
              Appointment slots are checked against the scheduling
              system before booking.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🔐</div>
            <h3>Verified Booking</h3>
            <p>
              Bookings are synchronized with the mock external
              healthcare system.
            </p>
          </div>

          <div className="feature-card">
            <div className="feature-icon">🎙️</div>
            <h3>Voice Assistance</h3>
            <p>
              Speak naturally using browser speech recognition and
              text-to-speech.
            </p>
          </div>
        </section>
      </main>

      <div className="footer">
        HealthAI Healthcare Platform • AI-assisted administrative
        healthcare access • Prototype
      </div>

      {/* QUESTIONNAIRE MODAL */}
      {showQuestionnaire && (
        <div className="questionnaire-overlay">
          <div className="questionnaire-card">
            <div className="questionnaire-header">
              <div>
                <h2>📝 Orthopedic Pre-Visit Questionnaire</h2>

                <p>
                  Please provide information to help your doctor
                  prepare for your appointment.
                </p>
              </div>

              <button
                className="questionnaire-close"
                onClick={() => setShowQuestionnaire(false)}
              >
                ×
              </button>
            </div>

            <div className="question-group">
              <label>
                1. Which body area is the reason for your visit?
                <span style={{ color: "#d33" }}> *</span>
              </label>

              <input
                value={questionnaireAnswers[1]}
                onChange={(event) =>
                  updateQuestionnaireAnswer(
                    1,
                    event.target.value
                  )
                }
                placeholder="Example: Knee"
              />
            </div>

            <div className="question-group">
              <label>
                2. When did you first notice the issue?
                <span style={{ color: "#d33" }}> *</span>
              </label>

              <input
                value={questionnaireAnswers[2]}
                onChange={(event) =>
                  updateQuestionnaireAnswer(
                    2,
                    event.target.value
                  )
                }
                placeholder="Example: About two weeks ago"
              />
            </div>

            <div className="question-group">
              <label>
                3. Have you previously consulted a doctor for
                this issue?
                <span style={{ color: "#d33" }}> *</span>
              </label>

              <select
                value={questionnaireAnswers[3]}
                onChange={(event) =>
                  updateQuestionnaireAnswer(
                    3,
                    event.target.value
                  )
                }
              >
                <option value="">
                  Select an answer
                </option>

                <option value="Yes">Yes</option>
                <option value="No">No</option>
              </select>
            </div>

            <div className="question-group">
              <label>
                4. Is there anything specific you want the doctor
                to know before the appointment?
              </label>

              <textarea
                rows="4"
                value={questionnaireAnswers[4]}
                onChange={(event) =>
                  updateQuestionnaireAnswer(
                    4,
                    event.target.value
                  )
                }
                placeholder="Optional"
              />
            </div>

            {questionnaireMessage && (
              <div className="questionnaire-message">
                {questionnaireMessage}
              </div>
            )}

            <button
              className="questionnaire-submit"
              onClick={submitQuestionnaire}
              disabled={questionnaireLoading}
            >
              {questionnaireLoading
                ? "Submitting..."
                : "Submit Questionnaire"}
            </button>
          </div>
        </div>
      )}

      {/* VOICE ASSISTANT */}
      {showVoice && (
        <VoiceAssistant
          onClose={() => setShowVoice(false)}
        />
      )}
    </div>
  );
}

export default App;
