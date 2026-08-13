import {
  ArrowRight,
  MapPin,
  Search,
  Stethoscope,
  UserRound,
  Users,
} from 'lucide-react';

import {
  useEffect,
  useMemo,
  useState,
} from 'react';

import {
  useNavigate,
} from 'react-router-dom';

import {
  EmptyState,
  PageHeader,
} from '../components/UI';

import {
  api,
} from '../lib/api';

import type {
  Patient,
} from '../lib/types';


// =====================================================
// PATIENT STATUS FILTER
// =====================================================

type PatientStatusFilter =
  | 'ALL'
  | 'ACTIVE'
  | 'INACTIVE';


// =====================================================
// PRESENTATION HELPERS
// =====================================================

function formatPatientStatus(
  status: string,
): string {
  return status
    .replaceAll(
      '_',
      ' ',
    )
    .toLowerCase()
    .replace(
      /\b\w/g,
      (
        letter,
      ) =>
        letter.toUpperCase(),
    );
}


// =====================================================
// ASSIGNED PATIENTS PAGE
// =====================================================

export default function PatientsPage() {
  const navigate =
    useNavigate();


  // ===================================================
  // PAGE STATE
  // ===================================================

  const [
    patients,
    setPatients,
  ] =
    useState<Patient[]>(
      [],
    );

  const [
    query,
    setQuery,
  ] =
    useState('');

  const [
    statusFilter,
    setStatusFilter,
  ] =
    useState<PatientStatusFilter>(
      'ALL',
    );

  const [
    loading,
    setLoading,
  ] =
    useState(true);

  const [
    error,
    setError,
  ] =
    useState('');


  // ===================================================
  // LOAD ASSIGNED PATIENTS
  //
  // The backend remains authoritative for assignment
  // access. Only patients actively assigned to the
  // authenticated clinician should be returned here.
  // ===================================================

  useEffect(
    () => {
      let active =
        true;

      async function loadPatients() {
        setLoading(
          true,
        );

        setError('');

        try {
          const response =
            await api.assignedPatients();

          if (!active) {
            return;
          }

          setPatients(
            response,
          );
        } catch (
          errorValue
        ) {
          if (!active) {
            return;
          }

          setPatients(
            [],
          );

          setError(
            errorValue instanceof Error
              ? errorValue.message
              : 'Unable to load your assigned patients.',
          );
        } finally {
          if (active) {
            setLoading(
              false,
            );
          }
        }
      }

      void loadPatients();

      return () => {
        active = false;
      };
    },
    [],
  );


  // ===================================================
  // PATIENT COUNTS
  // ===================================================

  const activePatientCount =
    useMemo(
      () =>
        patients.filter(
          (
            patient,
          ) =>
            patient.status
              .toUpperCase()
            === 'ACTIVE',
        ).length,
      [
        patients,
      ],
    );


  // ===================================================
  // SEARCH + STATUS FILTERING
  // ===================================================

  const filteredPatients =
    useMemo(
      () => {
        const normalisedQuery =
          query
            .trim()
            .toLowerCase();

        return patients.filter(
          (
            patient,
          ) => {
            // -------------------------------------------
            // STATUS
            // -------------------------------------------

            if (
              statusFilter
              !== 'ALL'
              &&
              patient.status
                .toUpperCase()
              !== statusFilter
            ) {
              return false;
            }


            // -------------------------------------------
            // SEARCH
            //
            // Search is deliberately broader than name
            // alone so the clinician can also locate a
            // patient by synthetic identifier or location.
            // -------------------------------------------

            if (
              !normalisedQuery
            ) {
              return true;
            }

            const searchableValue =
              [
                patient.first_name,
                patient.last_name,
                patient.synthetic_patient_number,
                patient.sex,
                patient.state,
                patient.lga,
                patient.status,
              ]
                .filter(Boolean)
                .join(' ')
                .toLowerCase();

            return searchableValue.includes(
              normalisedQuery,
            );
          },
        );
      },
      [
        patients,
        query,
        statusFilter,
      ],
    );


  // ===================================================
  // OPEN PATIENT INTELLIGENCE
  //
  // This routes to the clinician-only detailed patient
  // intelligence view containing demographics, clinical
  // history and stored LTFU prediction intelligence.
  // ===================================================

  function openPatient(
    patientId: string,
  ) {
    navigate(
      `/app/patients/${patientId}`,
    );
  }


  // ===================================================
  // RENDER
  // ===================================================

  return (
    <>
      <PageHeader
        eyebrow="Clinical caseload"
        title="Assigned patients"
        description="Review the synthetic patients actively assigned to your clinician account and open their longitudinal clinical and LTFU intelligence."
      />


      {/* =================================================
          CASELOAD SUMMARY
          ================================================= */}

      <section className="patient-caseload-summary">
        <div className="patient-summary-icon">
          <Users size={20} />
        </div>

        <div>
          <span className="eyebrow">
            Current portfolio
          </span>

          <strong>
            {
              loading
                ? 'Loading assigned patients…'
                : `${patients.length} assigned patient${
                    patients.length === 1
                      ? ''
                      : 's'
                  }`
            }
          </strong>

          <span>
            {
              loading
                ? 'Retrieving your active clinical assignments.'
                : `${activePatientCount} currently marked active`
            }
          </span>
        </div>

        <Stethoscope
          className="patient-summary-decoration"
          size={23}
        />
      </section>


      {/* =================================================
          SEARCH & FILTER TOOLBAR
          ================================================= */}

      <div className="patient-directory-toolbar">

        {/* -----------------------------------------------
            SEARCH
            ----------------------------------------------- */}

        <div className="patient-searchbox">
          <Search size={17} />

          <input
            type="search"
            placeholder="Search patient name, synthetic ID, state or LGA"
            value={query}
            onChange={
              (
                event,
              ) =>
                setQuery(
                  event.target.value,
                )
            }
          />
        </div>


        {/* -----------------------------------------------
            STATUS
            ----------------------------------------------- */}

        <select
          className="patient-status-filter"
          aria-label="Filter patients by status"
          value={
            statusFilter
          }
          onChange={
            (
              event,
            ) =>
              setStatusFilter(
                event.target.value as PatientStatusFilter,
              )
          }
        >
          <option value="ALL">
            All statuses
          </option>

          <option value="ACTIVE">
            Active
          </option>

          <option value="INACTIVE">
            Inactive
          </option>
        </select>
      </div>


      {/* =================================================
          ERROR
          ================================================= */}

      {error && (
        <div className="form-error patient-directory-error">
          {error}
        </div>
      )}


      {/* =================================================
          LOADING
          ================================================= */}

      {loading && (
        <div className="patient-loading-state">
          <div className="patient-loading-icon">
            <Stethoscope size={21} />
          </div>

          <strong>
            Loading clinical caseload
          </strong>

          <span>
            Retrieving your assigned synthetic patients…
          </span>
        </div>
      )}


      {/* =================================================
          EMPTY DIRECTORY
          ================================================= */}

      {!loading &&
        patients.length === 0 && (
          <EmptyState
            title="No assigned patients"
            description="Synthetic patients assigned to your clinician account will appear here."
          />
        )}


      {/* =================================================
          NO SEARCH RESULTS
          ================================================= */}

      {!loading &&
        patients.length > 0 &&
        filteredPatients.length === 0 && (
          <div className="patient-no-results">
            <Search size={22} />

            <strong>
              No matching patients
            </strong>

            <span>
              Try changing your search terms or status filter.
            </span>

            <button
              type="button"
              className="button secondary small"
              onClick={
                () => {
                  setQuery('');
                  setStatusFilter(
                    'ALL',
                  );
                }
              }
            >
              Clear filters
            </button>
          </div>
        )}


      {/* =================================================
          PATIENT DIRECTORY
          ================================================= */}

      {!loading &&
        filteredPatients.length > 0 && (
          <section className="patient-directory-section">
            <header className="patient-directory-heading">
              <div>
                <span className="eyebrow">
                  Assigned care portfolio
                </span>

                <h2>
                  Patient directory
                </h2>

                <p>
                  {
                    filteredPatients.length
                  } of {
                    patients.length
                  } assigned patient{
                    patients.length === 1
                      ? ''
                      : 's'
                  } shown
                </p>
              </div>
            </header>


            <div className="patient-grid">
              {
                filteredPatients.map(
                  (
                    patient,
                  ) => {
                    const initials =
                      `${
                        patient.first_name?.[0]
                        ?? ''
                      }${
                        patient.last_name?.[0]
                        ?? ''
                      }`
                        .toUpperCase();


                    return (
                      <button
                        type="button"
                        className="patient-card patient-card-button"
                        key={
                          patient.id
                        }
                        onClick={
                          () =>
                            openPatient(
                              patient.id,
                            )
                        }
                      >

                        {/* ---------------------------------
                            PATIENT HEADER
                            --------------------------------- */}

                        <div className="patient-card-header">
                          <div className="patient-avatar">
                            {
                              initials
                                ? (
                                  <span>
                                    {initials}
                                  </span>
                                )
                                : (
                                  <UserRound size={20} />
                                )
                            }
                          </div>

                          <span
                            className="status-chip"
                            data-status={
                              patient.status
                            }
                          >
                            {
                              formatPatientStatus(
                                patient.status,
                              )
                            }
                          </span>
                        </div>


                        {/* ---------------------------------
                            IDENTITY
                            --------------------------------- */}

                        <div className="patient-card-content">
                          <span className="patient-id">
                            {
                              patient
                                .synthetic_patient_number
                            }
                          </span>

                          <h3>
                            {
                              patient.first_name
                            }{' '}
                            {
                              patient.last_name
                            }
                          </h3>

                          <span className="patient-demographic">
                            {
                              patient.sex
                            }
                          </span>
                        </div>


                        {/* ---------------------------------
                            LOCATION
                            --------------------------------- */}

                        <div className="patient-location">
                          <MapPin size={14} />

                          <span>
                            {
                              patient.state
                            }
                            {' · '}
                            {
                              patient.lga
                            }
                          </span>
                        </div>


                        {/* ---------------------------------
                            ACTION
                            --------------------------------- */}

                        <div className="patient-card-action">
                          <span>
                            Open patient intelligence
                          </span>

                          <ArrowRight size={16} />
                        </div>
                      </button>
                    );
                  },
                )
              }
            </div>
          </section>
        )}
    </>
  );
}