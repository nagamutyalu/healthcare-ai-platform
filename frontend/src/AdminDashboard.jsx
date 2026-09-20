import { useEffect, useState } from "react";
import "./AdminDashboard.css";

const API = "http://localhost:8000";

function AdminDashboard() {
  const [hospital, setHospital] = useState(null);
  const [doctors, setDoctors] = useState([]);
  const [appointments, setAppointments] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // ==========================================
  // LOAD DASHBOARD DATA
  // ==========================================

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      const [
        hospitalResponse,
        doctorsResponse,
        appointmentsResponse,
      ] = await Promise.all([
        fetch(`${API}/hospitals/`),
        fetch(`${API}/doctors/`),
        fetch(`${API}/appointments/`),
      ]);

      if (!hospitalResponse.ok) {
        throw new Error("Unable to load hospital");
      }

      if (!doctorsResponse.ok) {
        throw new Error("Unable to load doctors");
      }

      if (!appointmentsResponse.ok) {
        throw new Error("Unable to load appointments");
      }

      const hospitalData = await hospitalResponse.json();
      const doctorData = await doctorsResponse.json();
      const appointmentData = await appointmentsResponse.json();

      setHospital(
        Array.isArray(hospitalData)
          ? hospitalData[0]
          : null
      );

      setDoctors(
        Array.isArray(doctorData)
          ? doctorData
          : []
      );

      setAppointments(
        Array.isArray(appointmentData)
          ? appointmentData
          : []
      );
    } catch (err) {
      console.error(err);

      setError(
        "Unable to load admin dashboard. Please make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, []);

  // ==========================================
  // APPOINTMENT COUNTS
  // ==========================================

  const confirmedCount = appointments.filter(
    (appointment) =>
      appointment.status === "CONFIRMED"
  ).length;

  const pendingCount = appointments.filter(
    (appointment) =>
      appointment.status === "PENDING"
  ).length;

  const cancelledCount = appointments.filter(
    (appointment) =>
      appointment.status === "CANCELLED"
  ).length;

  const rescheduledCount = appointments.filter(
    (appointment) =>
      appointment.status === "RESCHEDULED"
  ).length;

  // ==========================================
  // ANALYTICS
  // ==========================================

  const activeDoctors = doctors.filter(
    (doctor) => doctor.status === "ACTIVE"
  ).length;

  const confirmationRate =
    appointments.length > 0
      ? Math.round(
          (confirmedCount / appointments.length) * 100
        )
      : 0;

  const otherCount =
    appointments.length -
    confirmedCount -
    pendingCount -
    cancelledCount -
    rescheduledCount;

  // ==========================================
  // FORMAT DATE
  // ==========================================

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

  // ==========================================
  // FORMAT TIME
  // ==========================================

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

  // ==========================================
  // STATUS CLASS
  // ==========================================

  const statusClass = (status) => {
    switch (status) {
      case "CONFIRMED":
        return "admin-status confirmed";

      case "PENDING":
        return "admin-status pending";

      case "CANCELLED":
        return "admin-status cancelled";

      case "RESCHEDULED":
        return "admin-status rescheduled";

      default:
        return "admin-status";
    }
  };

  // ==========================================
  // LOADING
  // ==========================================

  if (loading) {
    return (
      <div className="admin-page">
        <div className="admin-loading">
          Loading admin dashboard...
        </div>
      </div>
    );
  }

  // ==========================================
  // ERROR
  // ==========================================

  if (error) {
    return (
      <div className="admin-page">
        <div className="admin-error">
          <p>{error}</p>

          <button
            onClick={loadDashboard}
            className="admin-retry"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // ==========================================
  // DASHBOARD
  // ==========================================

  return (
    <div className="admin-page">

      {/* ==========================================
          HEADER
          ========================================== */}

      <header className="admin-header">

        <div className="admin-brand">

          <div className="admin-logo">
            ✚
          </div>

          <div>
            <h1>
              HealthCare AI
            </h1>

            <span>
              Hospital Admin Portal
            </span>
          </div>

        </div>

        <div className="admin-online">
          <span></span>
          Admin Online
        </div>

      </header>

      {/* ==========================================
          MAIN
          ========================================== */}

      <main className="admin-main">

        {/* ==========================================
            WELCOME
            ========================================== */}

        <section className="admin-welcome">

          <div>

            <p className="admin-label">
              ADMIN DASHBOARD
            </p>

            <h2>
              Hospital Overview
            </h2>

            <p>
              Monitor hospital operations,
              doctors, and appointments.
            </p>

          </div>

          <button
            className="admin-refresh"
            onClick={loadDashboard}
          >
            ↻ Refresh
          </button>

        </section>

        {/* ==========================================
            HOSPITAL CARD
            ========================================== */}

        {hospital && (
          <section className="hospital-card">

            <div className="hospital-icon">
              🏥
            </div>

            <div className="hospital-info">

              <h3>
                {hospital.name}
              </h3>

              <p>
                {hospital.address},{" "}
                {hospital.city},{" "}
                {hospital.state}
              </p>

              <div className="hospital-details">

                <span>
                  📞 {hospital.phone}
                </span>

                <span>
                  🆔 Hospital ID:{" "}
                  {hospital.id}
                </span>

              </div>

            </div>

            <div className="hospital-approved">
              ✓ APPROVED
            </div>

          </section>
        )}

        {/* ==========================================
            STAT CARDS
            ========================================== */}

        <section className="admin-stats">

          <div className="admin-stat-card">

            <div className="admin-stat-icon blue">
              👨‍⚕️
            </div>

            <div>
              <span>
                Total Doctors
              </span>

              <strong>
                {doctors.length}
              </strong>
            </div>

          </div>

          <div className="admin-stat-card">

            <div className="admin-stat-icon green">
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

          <div className="admin-stat-card">

            <div className="admin-stat-icon purple">
              ✓
            </div>

            <div>
              <span>
                Confirmed
              </span>

              <strong>
                {confirmedCount}
              </strong>
            </div>

          </div>

          <div className="admin-stat-card">

            <div className="admin-stat-icon orange">
              ⏳
            </div>

            <div>
              <span>
                Pending
              </span>

              <strong>
                {pendingCount}
              </strong>
            </div>

          </div>

        </section>

        {/* ==========================================
            APPOINTMENT SUMMARY
            ========================================== */}

        <section className="admin-summary">

          <div className="summary-card">

            <div className="summary-icon confirmed-icon">
              ✓
            </div>

            <div>
              <strong>
                {confirmedCount}
              </strong>

              <span>
                Confirmed appointments
              </span>
            </div>

          </div>

          <div className="summary-card">

            <div className="summary-icon pending-icon">
              ⏳
            </div>

            <div>
              <strong>
                {pendingCount}
              </strong>

              <span>
                Pending appointments
              </span>
            </div>

          </div>

          <div className="summary-card">

            <div className="summary-icon cancelled-icon">
              ×
            </div>

            <div>
              <strong>
                {cancelledCount}
              </strong>

              <span>
                Cancelled appointments
              </span>
            </div>

          </div>

        </section>

        {/* ==========================================
            OPERATIONAL ANALYTICS
            ========================================== */}

        <section className="admin-card analytics-card">

          <div className="admin-card-header">

            <div>
              <h3>
                Operational Analytics
              </h3>

              <p>
                Current hospital appointment overview
              </p>
            </div>

            <span className="admin-count">
              Live Summary
            </span>

          </div>

          <div className="analytics-grid">

            {/* CONFIRMATION RATE */}

            <div className="analytics-item">

              <span className="analytics-label">
                Confirmation Rate
              </span>

              <strong className="analytics-value">
                {confirmationRate}%
              </strong>

              <div className="analytics-bar">

                <div
                  className="analytics-bar-fill confirmation"
                  style={{
                    width: `${confirmationRate}%`,
                  }}
                />

              </div>

            </div>

            {/* ACTIVE DOCTORS */}

            <div className="analytics-item">

              <span className="analytics-label">
                Active Doctors
              </span>

              <strong className="analytics-value">
                {activeDoctors}
              </strong>

              <p className="analytics-note">
                Currently active doctors
              </p>

            </div>

            {/* CONFIRMED */}

            <div className="analytics-item">

              <span className="analytics-label">
                Confirmed
              </span>

              <strong className="analytics-value">
                {confirmedCount}
              </strong>

              <div className="analytics-bar">

                <div
                  className="analytics-bar-fill confirmed"
                  style={{
                    width: `${
                      appointments.length
                        ? (confirmedCount /
                            appointments.length) *
                          100
                        : 0
                    }%`,
                  }}
                />

              </div>

            </div>

            {/* PENDING */}

            <div className="analytics-item">

              <span className="analytics-label">
                Pending
              </span>

              <strong className="analytics-value">
                {pendingCount}
              </strong>

              <div className="analytics-bar">

                <div
                  className="analytics-bar-fill pending"
                  style={{
                    width: `${
                      appointments.length
                        ? (pendingCount /
                            appointments.length) *
                          100
                        : 0
                    }%`,
                  }}
                />

              </div>

            </div>

          </div>

          {/* ANALYTICS FOOTER */}

          <div className="analytics-footer">

            <div>
              <span>
                Cancelled
              </span>

              <strong>
                {cancelledCount}
              </strong>
            </div>

            <div>
              <span>
                Rescheduled
              </span>

              <strong>
                {rescheduledCount}
              </strong>
            </div>

            <div>
              <span>
                Other Status
              </span>

              <strong>
                {otherCount}
              </strong>
            </div>

            <div>
              <span>
                Total
              </span>

              <strong>
                {appointments.length}
              </strong>
            </div>

          </div>

        </section>

        {/* ==========================================
            DOCTORS
            ========================================== */}

        <section className="admin-card">

          <div className="admin-card-header">

            <div>
              <h3>
                Doctors
              </h3>

              <p>
                Doctors registered with the hospital
              </p>
            </div>

            <span className="admin-count">
              {doctors.length} doctors
            </span>

          </div>

          {doctors.length === 0 ? (

            <div className="admin-empty">
              No doctors found.
            </div>

          ) : (

            <div className="doctor-grid">

              {doctors.map((doctor) => (

                <div
                  className="admin-doctor-card"
                  key={doctor.id}
                >

                  <div className="admin-doctor-avatar">
                    DR
                  </div>

                  <div className="admin-doctor-info">

                    <h4>
                      {doctor.name}
                    </h4>

                    <p>
                      {doctor.specialty}
                    </p>

                    <span>
                      {doctor.experience_years} years
                      experience
                    </span>

                  </div>

                  <div
                    className={
                      doctor.status === "ACTIVE"
                        ? "doctor-active-badge"
                        : "doctor-inactive-badge"
                    }
                  >
                    {doctor.status}
                  </div>

                </div>

              ))}

            </div>

          )}

        </section>

        {/* ==========================================
            RECENT APPOINTMENTS
            ========================================== */}

        <section className="admin-card">

          <div className="admin-card-header">

            <div>
              <h3>
                Recent Appointments
              </h3>

              <p>
                Latest appointment activity
              </p>
            </div>

            <span className="admin-count">
              {appointments.length} total
            </span>

          </div>

          {appointments.length === 0 ? (

            <div className="admin-empty">
              No appointments found.
            </div>

          ) : (

            <div className="admin-table-wrapper">

              <table className="admin-table">

                <thead>

                  <tr>

                    <th>
                      Appointment
                    </th>

                    <th>
                      Patient
                    </th>

                    <th>
                      Doctor
                    </th>

                    <th>
                      Date
                    </th>

                    <th>
                      Time
                    </th>

                    <th>
                      Status
                    </th>

                  </tr>

                </thead>

                <tbody>

                  {appointments
                    .slice()
                    .reverse()
                    .slice(0, 8)
                    .map((appointment) => {

                      const doctor =
                        doctors.find(
                          (item) =>
                            item.id ===
                            appointment.doctor_id
                        );

                      return (
                        <tr
                          key={appointment.id}
                        >

                          <td>
                            <strong>
                              #{appointment.id}
                            </strong>
                          </td>

                          <td>
                            Patient{" "}
                            {appointment.patient_id}
                          </td>

                          <td>
                            {doctor?.name ||
                              `Doctor ${appointment.doctor_id}`}
                          </td>

                          <td>
                            {formatDate(
                              appointment.start_time
                            )}
                          </td>

                          <td>
                            {formatTime(
                              appointment.start_time
                            )}
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

                        </tr>
                      );
                    })}

                </tbody>

              </table>

            </div>

          )}

        </section>

      </main>

      {/* ==========================================
          FOOTER
          ========================================== */}

      <footer className="admin-footer">
        Healthcare AI Platform • Hospital Admin Portal
      </footer>

    </div>
  );
}

export default AdminDashboard;
