import {
    AlertTriangle,
    CalendarDays,
    Check,
    CheckCircle2,
    ClipboardCheck,
    Clock3,
    FilePenLine,
    MessageSquareText,
    ShieldCheck,
    UserRound,
    X,
    XCircle,
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
// REVIEW DECISION TYPE
// =====================================================

type ReviewDecision =
    | 'APPROVE'
    | 'REJECT';


// =====================================================
// DISPLAY HELPERS
// =====================================================

function fieldLabel(
    value: string,
): string {
    return value
        .replaceAll(
            '_',
            ' ',
        )
        .replace(
            /\b\w/g,
            (
                letter,
            ) =>
                letter.toUpperCase(),
        );
}


function formatDateTime(
    value: string,
): string {
    return new Date(
        value,
    ).toLocaleString(
        [],
        {
            day: 'numeric',
            month: 'short',
            year: 'numeric',

            hour: '2-digit',
            minute: '2-digit',
        },
    );
}


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
        useState(
            true,
        );

    const [
        error,
        setError,
    ] =
        useState('');

    const [
        message,
        setMessage,
    ] =
        useState('');

    const [
        selected,
        setSelected,
    ] =
        useState<
            HealthRecordChangeRequest
            |
            null
        >(
            null,
        );


    // =================================================
    // REVIEW WORKFLOW STATE
    // =================================================

    const [
        reviewDecision,
        setReviewDecision,
    ] =
        useState<
            ReviewDecision
            |
            null
        >(
            null,
        );

    const [
        reviewComment,
        setReviewComment,
    ] =
        useState('');

    const [
        reviewing,
        setReviewing,
    ] =
        useState(
            false,
        );


    // ===================================================
    // LOAD PENDING REQUESTS
    // ===================================================

    useEffect(
        () => {
            let active =
                true;

            async function load() {
                setLoading(
                    true,
                );

                setError(
                    '',
                );

                try {
                    const response =
                        await api.pendingChangeRequests();

                    if (!active) {
                        return;
                    }

                    setRequests(
                        response,
                    );
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
                active =
                    false;
            };
        },
        [],
    );


    // ===================================================
    // SORT NEWEST REQUESTS FIRST
    // ===================================================

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


    // ===================================================
    // SELECT REQUEST
    //
    // Starting a new review always clears any decision or
    // comment left over from a previously selected request.
    // ===================================================

    function selectRequest(
        request:
            HealthRecordChangeRequest,
    ) {
        setSelected(
            request,
        );

        setReviewDecision(
            null,
        );

        setReviewComment(
            '',
        );

        setError(
            '',
        );

        setMessage(
            '',
        );
    }


    // ===================================================
    // START APPROVAL / REJECTION
    // ===================================================

    function beginReview(
        decision:
            ReviewDecision,
    ) {
        setReviewDecision(
            decision,
        );

        setReviewComment(
            '',
        );

        setError(
            '',
        );

        setMessage(
            '',
        );
    }


    // ===================================================
    // CANCEL CURRENT REVIEW
    // ===================================================

    function cancelReview() {
        if (reviewing) {
            return;
        }

        setReviewDecision(
            null,
        );

        setReviewComment(
            '',
        );
    }


    // ===================================================
    // SUBMIT REVIEW
    //
    // Approval intentionally requires a second deliberate
    // confirmation step. This protects against a clinician
    // accidentally modifying the authoritative record.
    //
    // Rejection requires a review comment so that the user
    // receives meaningful governance context.
    // ===================================================

    async function submitReview() {
        if (
            !selected
            ||
            !reviewDecision
        ) {
            return;
        }

        const comment =
            reviewComment
                .trim();

        if (
            reviewDecision
            === 'REJECT'
            &&
            !comment
        ) {
            setError(
                'Please provide a review comment explaining why the request is being rejected.',
            );

            return;
        }

        setReviewing(
            true,
        );

        setError(
            '',
        );

        setMessage(
            '',
        );

        try {
            const approve =
                reviewDecision
                === 'APPROVE';

            await api.reviewChangeRequest(
                selected.id,
                approve,
                comment
                || undefined,
            );


            // ---------------------------------------------
            // REMOVE REVIEWED REQUEST FROM PENDING QUEUE
            // ---------------------------------------------

            setRequests(
                (
                    current,
                ) =>
                    current.filter(
                        (
                            request,
                        ) =>
                            request.id
                            !== selected.id,
                    ),
            );


            // ---------------------------------------------
            // CLEAR REVIEW PANEL
            // ---------------------------------------------

            setSelected(
                null,
            );

            setReviewDecision(
                null,
            );

            setReviewComment(
                '',
            );


            setMessage(
                approve
                    ? (
                        'Change request approved. The authorised record has been updated and the review has been logged.'
                    )
                    : (
                        'Change request rejected. The authoritative record was not changed and the review has been logged.'
                    ),
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to review the change request.',
            );
        } finally {
            setReviewing(
                false,
            );
        }
    }


    // ===================================================
    // RENDER
    // ===================================================

    return (
        <>
            <PageHeader
                eyebrow="Clinical governance"
                title="Pending change requests"
                description="Review patient-submitted corrections before any authorised health information is changed."
            />


            {/* =================================================
                GOVERNANCE SUMMARY
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
                        {
                            requests.length > 0
                                ? 'Awaiting clinician review'
                                : 'Queue clear'
                        }
                    </strong>
                </div>


                <div>
                    <ShieldCheck size={20} />

                    <span>
                        Governance
                    </span>

                    <strong>
                        Clinician approval required
                    </strong>
                </div>
            </section>


            {/* =================================================
                SUCCESS / ERROR FEEDBACK
                ================================================= */}

            {message && (
                <div className="form-info page-message">
                    <CheckCircle2 size={17} />

                    {message}
                </div>
            )}


            {error && (
                <div className="form-error page-message">
                    {error}
                </div>
            )}


            {/* =================================================
                PAGE CONTENT
                ================================================= */}

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
                                description="The clinical-governance queue is clear. New patient-submitted corrections will appear here."
                            />
                        )
                        : (
                            <div className="change-request-layout">

                                {/* =====================================
                                    REQUEST QUEUE
                                    ===================================== */}

                                <section className="panel change-request-list">
                                    <div className="panel-heading">
                                        <div>
                                            <span className="eyebrow">
                                                Review queue
                                            </span>

                                            <h2>
                                                Requested corrections
                                            </h2>

                                            <p>
                                                Select a request to compare the
                                                stored and proposed values.
                                            </p>
                                        </div>

                                        <FilePenLine size={20} />
                                    </div>


                                    <div className="change-request-queue">
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
                                                                selectRequest(
                                                                    request,
                                                                )
                                                        }
                                                    >
                                                        <div className="change-request-card-main">
                                                            <span className="eyebrow">
                                                                {
                                                                    fieldLabel(
                                                                        request.field_name,
                                                                    )
                                                                }
                                                            </span>

                                                            <strong>
                                                                {
                                                                    request.proposed_value
                                                                }
                                                            </strong>

                                                            <small>
                                                                Submitted{' '}

                                                                {
                                                                    new Date(
                                                                        request.created_at,
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
                                    </div>
                                </section>


                                {/* =====================================
                                    REVIEW WORKSPACE
                                    ===================================== */}

                                <section className="panel change-request-detail">
                                    {
                                        selected
                                            ? (
                                                <>
                                                    {/* ---------------------
                                                        HEADER
                                                        --------------------- */}

                                                    <div className="panel-heading">
                                                        <div>
                                                            <span className="eyebrow">
                                                                Clinical review
                                                            </span>

                                                            <h2>
                                                                {
                                                                    fieldLabel(
                                                                        selected.field_name,
                                                                    )
                                                                }
                                                            </h2>

                                                            <p>
                                                                Compare the currently
                                                                stored value with the
                                                                patient's proposed
                                                                correction.
                                                            </p>
                                                        </div>

                                                        <ClipboardCheck size={20} />
                                                    </div>


                                                    {/* ---------------------
                                                        REQUEST IDENTITY
                                                        --------------------- */}

                                                    <div className="change-request-context">
                                                        <div>
                                                            <span>
                                                                Patient
                                                            </span>

                                                            <strong>
                                                                {
                                                                    selected.patient_id
                                                                }
                                                            </strong>
                                                        </div>

                                                        <div>
                                                            <span>
                                                                Request
                                                            </span>

                                                            <strong className="change-request-id">
                                                                {
                                                                    selected.id
                                                                }
                                                            </strong>
                                                        </div>
                                                    </div>


                                                    {/* ---------------------
                                                        BEFORE / AFTER
                                                        --------------------- */}

                                                    <div className="change-value-comparison">
                                                        <div className="change-value-card current">
                                                            <span>
                                                                Current value
                                                            </span>

                                                            <strong>
                                                                {
                                                                    selected.previous_value
                                                                    ??
                                                                    'Not recorded'
                                                                }
                                                            </strong>

                                                            <small>
                                                                Authoritative stored value
                                                            </small>
                                                        </div>


                                                        <div className="change-value-arrow">
                                                            →
                                                        </div>


                                                        <div className="change-value-card proposed">
                                                            <span>
                                                                Proposed value
                                                            </span>

                                                            <strong>
                                                                {
                                                                    selected.proposed_value
                                                                }
                                                            </strong>

                                                            <small>
                                                                Patient-requested correction
                                                            </small>
                                                        </div>
                                                    </div>


                                                    {/* ---------------------
                                                        USER REASON
                                                        --------------------- */}

                                                    <div className="change-request-reason">
                                                        <div className="change-request-section-title">
                                                            <MessageSquareText size={16} />

                                                            <span>
                                                                Reason supplied by user
                                                            </span>
                                                        </div>

                                                        <p>
                                                            {
                                                                selected.reason
                                                                ||
                                                                'No additional reason was supplied.'
                                                            }
                                                        </p>
                                                    </div>


                                                    {/* ---------------------
                                                        METADATA
                                                        --------------------- */}

                                                    <div className="change-request-meta">
                                                        <span>
                                                            <UserRound size={14} />

                                                            Requested by{' '}

                                                            {
                                                                selected.requested_by
                                                            }
                                                        </span>

                                                        <span>
                                                            <CalendarDays size={14} />

                                                            {
                                                                formatDateTime(
                                                                    selected.created_at,
                                                                )
                                                            }
                                                        </span>
                                                    </div>


                                                    {/* ---------------------
                                                        GOVERNANCE NOTICE
                                                        --------------------- */}

                                                    <div className="change-request-governance-note">
                                                        <ShieldCheck size={18} />

                                                        <span>
                                                            Approval updates the authorised
                                                            patient record. Rejection leaves
                                                            the record unchanged. Both
                                                            decisions are recorded in the
                                                            audit trail.
                                                        </span>
                                                    </div>


                                                    {/* =================================
                                                        INITIAL DECISION ACTIONS
                                                        ================================= */}

                                                    {!reviewDecision && (
                                                        <div className="change-review-actions">
                                                            <button
                                                                type="button"
                                                                className="button danger-outline"
                                                                onClick={
                                                                    () =>
                                                                        beginReview(
                                                                            'REJECT',
                                                                        )
                                                                }
                                                            >
                                                                <XCircle size={17} />

                                                                Reject request
                                                            </button>


                                                            <button
                                                                type="button"
                                                                className="button primary"
                                                                onClick={
                                                                    () =>
                                                                        beginReview(
                                                                            'APPROVE',
                                                                        )
                                                                }
                                                            >
                                                                <Check size={17} />

                                                                Approve request
                                                            </button>
                                                        </div>
                                                    )}


                                                    {/* =================================
                                                        REVIEW CONFIRMATION PANEL
                                                        ================================= */}

                                                    {reviewDecision && (
                                                        <div
                                                            className="change-review-panel"
                                                            data-decision={
                                                                reviewDecision
                                                            }
                                                        >
                                                            <div className="change-review-panel-heading">
                                                                <div className="change-review-decision-icon">
                                                                    {
                                                                        reviewDecision
                                                                            === 'APPROVE'
                                                                            ? (
                                                                                <CheckCircle2 size={20} />
                                                                            )
                                                                            : (
                                                                                <AlertTriangle size={20} />
                                                                            )
                                                                    }
                                                                </div>


                                                                <div>
                                                                    <strong>
                                                                        {
                                                                            reviewDecision
                                                                                === 'APPROVE'
                                                                                ? 'Confirm approval'
                                                                                : 'Reject this request'
                                                                        }
                                                                    </strong>

                                                                    <span>
                                                                        {
                                                                            reviewDecision
                                                                                === 'APPROVE'
                                                                                ? (
                                                                                    'Approving this request will update the authorised record with the proposed value.'
                                                                                )
                                                                                : (
                                                                                    'The authoritative record will remain unchanged.'
                                                                                )
                                                                        }
                                                                    </span>
                                                                </div>


                                                                <button
                                                                    type="button"
                                                                    className="icon-button"
                                                                    disabled={
                                                                        reviewing
                                                                    }
                                                                    onClick={
                                                                        cancelReview
                                                                    }
                                                                    aria-label="Cancel review decision"
                                                                >
                                                                    <X size={17} />
                                                                </button>
                                                            </div>


                                                            <label className="change-review-comment">
                                                                <span>
                                                                    Review comment

                                                                    {
                                                                        reviewDecision
                                                                            === 'REJECT'
                                                                            ? ' *'
                                                                            : ' (optional)'
                                                                    }
                                                                </span>

                                                                <textarea
                                                                    rows={4}
                                                                    maxLength={2000}
                                                                    value={
                                                                        reviewComment
                                                                    }
                                                                    disabled={
                                                                        reviewing
                                                                    }
                                                                    placeholder={
                                                                        reviewDecision
                                                                            === 'APPROVE'
                                                                            ? (
                                                                                'Optional note explaining the clinical review...'
                                                                            )
                                                                            : (
                                                                                'Explain why this correction cannot be approved...'
                                                                            )
                                                                    }
                                                                    onChange={
                                                                        (
                                                                            event,
                                                                        ) =>
                                                                            setReviewComment(
                                                                                event.target.value,
                                                                            )
                                                                    }
                                                                />

                                                                <small>
                                                                    {
                                                                        reviewComment.length
                                                                    } / 2000
                                                                </small>
                                                            </label>


                                                            <div className="change-review-confirm-actions">
                                                                <button
                                                                    type="button"
                                                                    className="button secondary"
                                                                    disabled={
                                                                        reviewing
                                                                    }
                                                                    onClick={
                                                                        cancelReview
                                                                    }
                                                                >
                                                                    Cancel
                                                                </button>


                                                                <button
                                                                    type="button"
                                                                    className={
                                                                        reviewDecision
                                                                            === 'APPROVE'
                                                                            ? 'button primary'
                                                                            : 'button danger'
                                                                    }
                                                                    disabled={
                                                                        reviewing
                                                                        ||
                                                                        (
                                                                            reviewDecision
                                                                            === 'REJECT'
                                                                            &&
                                                                            !reviewComment.trim()
                                                                        )
                                                                    }
                                                                    onClick={
                                                                        submitReview
                                                                    }
                                                                >
                                                                    {
                                                                        reviewDecision
                                                                            === 'APPROVE'
                                                                            ? (
                                                                                <CheckCircle2 size={17} />
                                                                            )
                                                                            : (
                                                                                <XCircle size={17} />
                                                                            )
                                                                    }

                                                                    {
                                                                        reviewing
                                                                            ? 'Saving review…'
                                                                            : reviewDecision
                                                                                === 'APPROVE'
                                                                                ? 'Confirm approval'
                                                                                : 'Confirm rejection'
                                                                    }
                                                                </button>
                                                            </div>
                                                        </div>
                                                    )}
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
                                                        compare its current and proposed
                                                        values before making a clinical
                                                        governance decision.
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
