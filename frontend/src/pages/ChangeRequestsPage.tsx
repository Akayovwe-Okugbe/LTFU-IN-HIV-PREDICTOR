import {
    CalendarDays,
    CheckCircle2,
    ClipboardCheck,
    Clock3,
    FilePenLine,
    UserRound,
} from 'lucide-react';

import {
    useEffect,
    useMemo,
    useState,
} from 'react';

import {
    EmptyState,
    PageHeader,
} from '../components/UI';

import {
    api,
} from '../lib/api';

import type {
    HealthRecordChangeRequest,
} from '../lib/types';


// =====================================================
// PAGE
// =====================================================

export default function ChangeRequestsPage() {
    const [
        requests,
        setRequests,
    ] =
        useState<
            HealthRecordChangeRequest[]
        >(
            [],
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

    const [
        selected,
        setSelected,
    ] =
        useState<
            HealthRecordChangeRequest | null
        >(
            null,
        );


    // ===================================================
    // LOAD REQUESTS
    // ===================================================

    useEffect(
        () => {
            let active =
                true;

            async function load() {
                try {
                    const response =
                        await api.pendingChangeRequests();

                    if (active) {
                        setRequests(
                            response,
                        );
                    }
                } catch (
                errorValue
                ) {
                    if (active) {
                        setError(
                            errorValue instanceof Error
                                ? errorValue.message
                                : 'Unable to load change requests.',
                        );
                    }
                } finally {
                    if (active) {
                        setLoading(
                            false,
                        );
                    }
                }
            }

            void load();

            return () => {
                active = false;
            };
        },
        [],
    );


    const sortedRequests =
        useMemo(
            () =>
                [...requests]
                    .sort(
                        (
                            first,
                            second,
                        ) =>
                            new Date(
                                second.created_at,
                            ).getTime()
                            -
                            new Date(
                                first.created_at,
                            ).getTime(),
                    ),
            [
                requests,
            ],
        );


    return (
        <>
            <PageHeader
                eyebrow="Clinical governance"
                title="Pending change requests"
                description="Review corrections submitted by users linked to patients within your permitted clinical workflow."
            />


            {/* =================================================
          SUMMARY
          ================================================= */}

            <section className="change-request-summary">
                <div>
                    <ClipboardCheck size={20} />

                    <span>
                        Pending requests
                    </span>

                    <strong>
                        {
                            requests.length
                        }
                    </strong>
                </div>

                <div>
                    <Clock3 size={20} />

                    <span>
                        Review state
                    </span>

                    <strong>
                        Awaiting clinician review
                    </strong>
                </div>

                <div>
                    <CheckCircle2 size={20} />

                    <span>
                        Governance
                    </span>

                    <strong>
                        Authoritative record unchanged
                    </strong>
                </div>
            </section>


            {error && (
                <div className="form-error page-message">
                    {error}
                </div>
            )}


            {
                loading
                    ? (
                        <div className="change-request-loading">
                            Loading pending requests…
                        </div>
                    )
                    : sortedRequests.length
                        === 0
                        ? (
                            <EmptyState
                                title="No requests awaiting review"
                                description="New patient-submitted corrections will appear here for clinician review."
                            />
                        )
                        : (
                            <div className="change-request-layout">

                                {/* ---------------------------------------
                    REQUEST DIRECTORY
                    --------------------------------------- */}

                                <section className="panel change-request-list">
                                    <div className="panel-heading">
                                        <div>
                                            <span className="eyebrow">
                                                Review queue
                                            </span>

                                            <h2>
                                                Requested corrections
                                            </h2>
                                        </div>

                                        <FilePenLine size={20} />
                                    </div>


                                    {
                                        sortedRequests.map(
                                            (
                                                request,
                                            ) => (
                                                <button
                                                    type="button"
                                                    key={
                                                        request.id
                                                    }
                                                    className={
                                                        selected?.id
                                                            === request.id
                                                            ? 'change-request-card active'
                                                            : 'change-request-card'
                                                    }
                                                    onClick={
                                                        () =>
                                                            setSelected(
                                                                request,
                                                            )
                                                    }
                                                >
                                                    <div>
                                                        <span className="eyebrow">
                                                            {
                                                                request.field_name
                                                                    .replaceAll(
                                                                        '_',
                                                                        ' ',
                                                                    )
                                                            }
                                                        </span>

                                                        <strong>
                                                            {
                                                                request
                                                                    .proposed_value
                                                            }
                                                        </strong>

                                                        <small>
                                                            Submitted{' '}
                                                            {
                                                                new Date(
                                                                    request
                                                                        .created_at,
                                                                )
                                                                    .toLocaleDateString()
                                                            }
                                                        </small>
                                                    </div>

                                                    <span
                                                        className="change-request-status"
                                                        data-status={
                                                            request.status
                                                        }
                                                    >
                                                        {
                                                            request.status
                                                        }
                                                    </span>
                                                </button>
                                            ),
                                        )
                                    }
                                </section>


                                {/* ---------------------------------------
                    DETAIL
                    --------------------------------------- */}

                                <section className="panel change-request-detail">
                                    {
                                        selected
                                            ? (
                                                <>
                                                    <div className="panel-heading">
                                                        <div>
                                                            <span className="eyebrow">
                                                                Request detail
                                                            </span>

                                                            <h2>
                                                                Proposed record correction
                                                            </h2>
                                                        </div>

                                                        <ClipboardCheck size={20} />
                                                    </div>


                                                    <div className="change-request-detail-grid">
                                                        <div>
                                                            <span>
                                                                Field
                                                            </span>

                                                            <strong>
                                                                {
                                                                    selected
                                                                        .field_name
                                                                        .replaceAll(
                                                                            '_',
                                                                            ' ',
                                                                        )
                                                                }
                                                            </strong>
                                                        </div>

                                                        <div>
                                                            <span>
                                                                Patient ID
                                                            </span>

                                                            <strong>
                                                                {
                                                                    selected.patient_id
                                                                }
                                                            </strong>
                                                        </div>

                                                        <div>
                                                            <span>
                                                                Current value
                                                            </span>

                                                            <strong>
                                                                {
                                                                    selected
                                                                        .previous_value
                                                                    ??
                                                                    'Not recorded'
                                                                }
                                                            </strong>
                                                        </div>

                                                        <div>
                                                            <span>
                                                                Proposed value
                                                            </span>

                                                            <strong>
                                                                {
                                                                    selected
                                                                        .proposed_value
                                                                }
                                                            </strong>
                                                        </div>
                                                    </div>


                                                    <div className="change-request-reason">
                                                        <span>
                                                            Reason supplied
                                                        </span>

                                                        <p>
                                                            {
                                                                selected.reason
                                                                ||
                                                                'No additional reason was supplied.'
                                                            }
                                                        </p>
                                                    </div>


                                                    <div className="change-request-meta">
                                                        <span>
                                                            <UserRound size={14} />

                                                            Requested by{' '}
                                                            {
                                                                selected
                                                                    .requested_by
                                                            }
                                                        </span>

                                                        <span>
                                                            <CalendarDays size={14} />

                                                            {
                                                                new Date(
                                                                    selected
                                                                        .created_at,
                                                                )
                                                                    .toLocaleString()
                                                            }
                                                        </span>
                                                    </div>


                                                    <div className="change-request-governance-note">
                                                        <ClipboardCheck size={18} />

                                                        <span>
                                                            The authoritative clinical
                                                            record remains unchanged until
                                                            an authorised review workflow
                                                            approves the request.
                                                        </span>
                                                    </div>
                                                </>
                                            )
                                            : (
                                                <div className="empty-mini">
                                                    <ClipboardCheck />

                                                    <h3>
                                                        Select a request
                                                    </h3>

                                                    <p>
                                                        Choose a pending correction to
                                                        inspect its proposed values and
                                                        supporting context.
                                                    </p>
                                                </div>
                                            )
                                    }
                                </section>
                            </div>
                        )
            }
        </>
    );
}
