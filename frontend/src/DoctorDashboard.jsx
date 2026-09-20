import { useEffect, useState } from "react";
import "./DoctorDashboard.css";

const API = "https://healthcare-ai-platform-qr5x.onrender.com";
const BACKEND_API = "https://healthcare-ai-platform-qr5x.onrender.com";
const DOCTOR_ID = 1;

function DoctorDashboard() {
  const [doctor, setDoctor] = useState(null);
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [questionnaireResponses, setQuestionnaireResponses] =
    useState([]);

  const [selectedAppointment, setSelectedAppointment] =
    useState(null);

  const [questionnaireLoading, setQuestionnaireLoading] =
    useState(false);

  const [questionnaireError, setQuestionnaireError] =
    useState("");

  // ==================================================
  // LOAD DOCTOR DASHBOARD
  // ==================================================

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      const DEMO_DOCTOR = {
        id: 1,
        name: "Dr. Rao",
        specialty: "Orthopedics",
        department: "Orthopedics",
        hospital_id: 2,
        qualifications: "MBBS, MS Orthopedics",
        experience_years: 10,
        languages: "English, Telugu",
        consultation_type: "IN_PERSON",
        consultation_duration: 30,
        status: "ACTIVE"
      };

      const DEMO_APPOINTMENT = {
        id: 1,
        hospital_id: 2,
        doctor_id: 1,
        patient_id: 1,
        appointment_type: "IN_PERSON",
        start_time: "2026-09-21T09:00:00",
        end_time: "2026-09-21T09:30:00",
        status: "CONFIRMED",
        external_appointment_id: "EHR-DEMO001"
      };

      const [doctorResponse, appointmentsResponse] =
        await Promise.all([
          fetch(`${API}/doctors/${DOCTOR_ID}`),
          fetch(`${API}/appointments/?doctor_id=${DOCTOR_ID}`)
        ]);

      let doctorData = null;
      let appointmentData = [];

      if (doctorResponse.ok) {
        const data = await doctorResponse.json();
        if (data && data.name) doctorData = data;
      }

      if (appointmentsResponse.ok) {
        const data = await appointmentsResponse.json();
        if (Array.isArray(data)) {
          appointmentData = data.filter(
            (a) => Number(a.doctor_id) === DOCTOR_ID
          );
        }
      }

      setDoctor(doctorData || DEMO_DOCTOR);
      setAppointments(
        appointmentData.length > 0
          ? appointmentData
          : [DEMO_APPOINTMENT]
      );

    } catch (err) {
      console.error(err);

      setDoctor({
        id: 1,
        name: "Dr. Rao",
        specialty: "Orthopedics",
        department: "Orthopedics",
        hospital_id: 2,
        qualifications: "MBBS, MS Orthopedics",
        experience_years: 10,
        languages: "English, Telugu",
        consultation_type: "IN_PERSON",
        consultation_duration: 30,
        status: "ACTIVE"
      });

      setAppointments([{
        id: 1,
        hospital_id: 2,
        doctor_id: 1,
        patient_id: 1,
        appointment_type: "IN_PERSON",
        start_time: "2026-09-21T09:00:00",
        end_time: "2026-09-21T09:30:00",
        status: "CONFIRMED",
        external_appointment_id: "EHR-DEMO001"
      }]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  // ==================================================
  // LOAD QUESTIONNAIRE RESPONSES
  // ==================================================

  const viewQuestionnaire = async (appointment) => {
    try {
      setSelectedAppointment(appointment);
      setQuestionnaireResponses([]);
      setQuestionnaireError("");
      setQuestionnaireLoading(true);

      const response = await fetch(
        `https://healthcare-ai-platform-qr5x.onrender.com/questionnaire-responses/appointment/${appointment.id}`
      );

      if (!response.ok) {
        throw new Error(
          `Unable to load questionnaire: ${response.status}`
        );
      }

      const data = await response.json();

      console.log(
        "QUESTIONNAIRE RESPONSES:",
        data
      );

      setQuestionnaireResponses(
        Array.isArray(data) ? data : []
      );
    } catch (err) {
      console.error(
        "QUESTIONNAIRE ERROR:",
        err
      );

      setQuestionnaireError(
        "Unable to load questionnaire responses."
      );
    } finally {
      setQuestionnaireLoading(false);
    }
  };

  // ==================================================
  // CLOSE QUESTIONNAIRE
  // ==================================================

  const closeQuestionnaire = () => {
    setSelectedAppointment(null);
    setQuestionnaireResponses([]);
    setQuestionnaireError("");
  };

  // ==================================================
  // APPOINTMENT COUNTS
  // ==================================================

  const confirmedAppointments =
    appointments.filter(
      (appointment) =>
        appointment.status === "CONFIRMED"
    );

  const pendingAppointments =
    appointments.filter(
      (appointment) =>
        appointment.status === "PENDING"
    );

  const cancelledAppointments =
    appointments.filter(
      (appointment) =>
        appointment.status === "CANCELLED"
    );

  // ==================================================
  // FORMAT DATE
  // ==================================================

  const formatDate = (value) => {
    if (!value) return "-";

    return new Date(value).toLocaleDateString(
      "en-IN",
      {
        day: "2-digit",
        month: "short",
        year: "numeric",
      }
    );
  };

  // ==================================================
  // FORMAT TIME
  // ==================================================

  const formatTime = (value) => {
    if (!value) return "-";

    return new Date(value).toLocaleTimeString(
      "en-IN",
      {
        hour: "numeric",
        minute: "2-digit",
      }
    );
  };

  // ==================================================
  // STATUS CLASS
  // ==================================================

  const statusClass = (status) => {
    switch (status) {
      case "CONFIRMED":
        return "doctor-status confirmed";

      case "PENDING":
        return "doctor-status pending";

      case "CANCELLED":
        return "doctor-status cancelled";

      case "RESCHEDULED":
        return "doctor-status rescheduled";

      default:
        return "doctor-status";
    }
  };

  // ==================================================
  // LOADING
  // ==================================================

  if (loading) {
    return (
      <div className="doctor-page">
        <div className="doctor-loading">
          Loading doctor dashboard...
        </div>
      </div>
    );
  }

  // ==================================================
  // ERROR
  // ==================================================

  if (error) {
    return (
      <div className="doctor-page">
        <div className="doctor-error">
          {error}

          <button
            onClick={loadDashboard}
            className="doctor-retry"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // ==================================================
  // UI
  // ==================================================

  return (
    <div className="doctor-page">

      {/* HEADER */}
      <header className="doctor-header">

        <div className="doctor-brand">

          <div className="doctor-logo">
            ✚
          </div>

          <div>
            <h1>
              HealthCare AI
            </h1>

            <span>
              Doctor Portal
            </span>
          </div>

        </div>

        <div className="doctor-online">
          <span></span>
          Online
        </div>

      </header>

      {/* MAIN */}
      <main className="doctor-main">

        {/* WELCOME */}
        <section className="doctor-welcome">

          <div>

            <p className="doctor-label">
              DOCTOR DASHBOARD
            </p>

            <h2>
              Welcome, {doctor?.name || "Doctor"}
            </h2>

            <p>
              Manage appointments and view
              patient information.
            </p>

          </div>

          <button
            className="refresh-button"
            onClick={loadDashboard}
          >
            ↻ Refresh
          </button>

        </section>

        {/* DOCTOR PROFILE */}
        {doctor && (
          <section className="doctor-profile">

            <div className="profile-avatar">
              DR
            </div>

            <div className="profile-info">

              <h3>
                {doctor.name}
              </h3>

              <p>
                {doctor.specialty}
              </p>

              <div className="profile-details">

                <span>
                  🏥 Hospital ID:{" "}
                  {doctor.hospital_id}
                </span>

                <span>
                  🎓 {doctor.qualifications}
                </span>

                <span>
                  💼 {doctor.experience_years} years
                  experience
                </span>

                <span>
                  🗣️ {doctor.languages}
                </span>

              </div>

            </div>

            <div className="doctor-active">
              ACTIVE
            </div>

          </section>
        )}

        {/* STAT CARDS */}
        <section className="doctor-stats">

          <div className="doctor-stat-card">

            <div className="stat-icon blue">
              📅
            </div>

            <div>
              <span>
                Total Appointments
              </span>

              <strong>
                {appointments.length}
              </strong>
            </div>

          </div>

          <div className="doctor-stat-card">

            <div className="stat-icon green">
              ✓
            </div>

            <div>
              <span>
                Confirmed
              </span>

              <strong>
                {confirmedAppointments.length}
              </strong>
            </div>

          </div>

          <div className="doctor-stat-card">

            <div className="stat-icon orange">
              ⏳
            </div>

            <div>
              <span>
                Pending
              </span>

              <strong>
                {pendingAppointments.length}
              </strong>
            </div>

          </div>

          <div className="doctor-stat-card">

            <div className="stat-icon red">
              ×
            </div>

            <div>
              <span>
                Cancelled
              </span>

              <strong>
                {cancelledAppointments.length}
              </strong>
            </div>

          </div>

        </section>

        {/* APPOINTMENTS */}
        <section className="appointments-card">

          <div className="appointments-header">

            <div>

              <h3>
                Appointments
              </h3>

              <p>
                Patient appointments for Dr.{" "}
                {doctor?.name || "Doctor"}
              </p>

            </div>

            <span className="appointment-count">
              {appointments.length} total
            </span>

          </div>

          {appointments.length === 0 ? (

            <div className="empty-appointments">

              <div>
                📅
              </div>

              <h4>
                No appointments
              </h4>

              <p>
                There are no appointments
                available for this doctor.
              </p>

            </div>

          ) : (

            <div className="appointment-table-wrapper">

              <table className="appointment-table">

                <thead>

                  <tr>

                    <th>
                      Appointment
                    </th>

                    <th>
                      Patient
                    </th>

                    <th>
                      Date
                    </th>

                    <th>
                      Time
                    </th>

                    <th>
                      Type
                    </th>

                    <th>
                      Status
                    </th>

                    <th>
                      Questionnaire
                    </th>

                  </tr>

                </thead>

                <tbody>

                  {appointments.map(
                    (appointment) => (

                      <tr
                        key={appointment.id}
                      >

                        <td>

                          <strong>
                            #{appointment.id}
                          </strong>

                        </td>

                        <td>

                          <div className="patient-cell">

                            <div className="patient-avatar">
                              P
                            </div>

                            <div>

                              <strong>
                                Patient{" "}
                                {appointment.patient_id}
                              </strong>

                              <small>
                                ID:{" "}
                                {appointment.patient_id}
                              </small>

                            </div>

                          </div>

                        </td>

                        <td>
                          {formatDate(
                            appointment.start_time
                          )}
                        </td>

                        <td>

                          <strong>
                            {formatTime(
                              appointment.start_time
                            )}
                          </strong>

                          <small className="time-end">
                            to{" "}
                            {formatTime(
                              appointment.end_time
                            )}
                          </small>

                        </td>

                        <td>

                          <span className="type-badge">

                            {appointment.appointment_type
                              ?.replace(
                                "_",
                                " "
                              )}

                          </span>

                        </td>

                        <td>

                          <span
                            className={statusClass(
                              appointment.status
                            )}
                          >
                            {appointment.status}
                          </span>

                        </td>

                        <td>

                          <button
                            className="questionnaire-button"
                            onClick={() =>
                              viewQuestionnaire(
                                appointment
                              )
                            }
                          >
                            📋 View
                          </button>

                        </td>

                      </tr>

                    )
                  )}

                </tbody>

              </table>

            </div>

          )}

        </section>

        {/* QUESTIONNAIRE INFO */}
        <section className="doctor-info-card">

          <div className="info-icon">
            📋
          </div>

          <div>

            <h3>
              Pre-Visit Questionnaire
            </h3>

            <p>
              Patient questionnaire responses are
              collected before the consultation and
              can be viewed from the appointment list.
            </p>

          </div>

          <div className="info-status">
            Available
          </div>

        </section>

      </main>

      {/* QUESTIONNAIRE MODAL */}
      {selectedAppointment && (

        <div
          className="questionnaire-overlay"
          onClick={closeQuestionnaire}
        >

          <div
            className="questionnaire-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >

            <div className="questionnaire-modal-header">

              <div>

                <p className="questionnaire-label">
                  PRE-VISIT QUESTIONNAIRE
                </p>

                <h2>
                  Appointment #
                  {selectedAppointment.id}
                </h2>

                <span>
                  Patient{" "}
                  {selectedAppointment.patient_id}
                </span>

              </div>

              <button
                className="questionnaire-close"
                onClick={closeQuestionnaire}
              >
                ×
              </button>

            </div>

            <div className="questionnaire-modal-body">

              {questionnaireLoading && (

                <div className="questionnaire-loading">
                  Loading questionnaire responses...
                </div>

              )}

              {questionnaireError && (

                <div className="questionnaire-error">
                  {questionnaireError}
                </div>

              )}

              {!questionnaireLoading &&
                !questionnaireError &&
                questionnaireResponses.length === 0 && (

                  <div className="questionnaire-empty">

                    <div>
                      📋
                    </div>

                    <h3>
                      No responses yet
                    </h3>

                    <p>
                      This patient has not submitted
                      questionnaire responses for
                      this appointment.
                    </p>

                  </div>

                )}

              {!questionnaireLoading &&
                !questionnaireError &&
                questionnaireResponses.length > 0 && (

                  <div className="questionnaire-list">

                    {questionnaireResponses.map(
                      (response, index) => (

                        <div
                          className="questionnaire-answer"
                          key={
                            response.id || index
                          }
                        >

                          <div className="answer-number">
                            {index + 1}
                          </div>

                          <div className="answer-content">

                            <span>
                              Question{" "}
                              {index + 1}
                            </span>

                            <p>
                              {response.answer ||
                                "No answer provided"}
                            </p>

                          </div>

                        </div>

                      )
                    )}

                  </div>

                )}

            </div>

            <div className="questionnaire-modal-footer">

              <button
                className="questionnaire-done"
                onClick={closeQuestionnaire}
              >
                Close
              </button>

            </div>

          </div>

        </div>

      )}

      <footer className="doctor-footer">
        Healthcare AI Platform • Doctor Portal
      </footer>

    </div>
  );
}

export default DoctorDashboard;
