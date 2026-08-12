import {
    Activity,
    AlertTriangle,
    CheckCircle2,
    ChevronDown,
    ChevronRight,
    Clock3,
    Filter,
    Globe2,
    Search,
    ShieldCheck,
    UserRound,
    X,
} from 'lucide-react';

import {
    useEffect,
    useMemo,
    useState,
} from 'react';

import {
    PageHeader,
} from '../components/UI';

import {
    useAuth,
} from '../context/AuthContext';

import {
    api,
} from '../lib/api';

import type {
    AuditLogItem,
    AuditLogMetadata,
} from '../lib/types';


// =====================================================
// CONSTANTS
// =====================================================

const PAGE_SIZE =
    25;


// =====================================================
// PRESENTATION HELPERS
// =====================================================

function humaniseValue(
    value: string,
): string {
    return value
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


function formatAuditDate(
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
// AUDIT LOGS PAGE
// =====================================================

export default function AuditLogsPage() {
    const {
        user,
    } =
        useAuth();


    // ===================================================
    // FAIL-CLOSED FRONTEND ROLE CHECK
    //
    // Backend RBAC remains authoritative. This additional
    // check prevents accidental rendering of administrator
    // controls for another role.
    // ===================================================

    if (
        user?.role
        !== 'ADMINISTRATOR'
    ) {
        return (
            <section className="panel audit-access-denied">
                <ShieldCheck size={28} />

                <h2>
                    Administrator access required
                </h2>

                <p>
                    Audit-log review is restricted to MEDISCOPE
                    administrators.
                </p>
            </section>
        );
    }

    return (
        <AdministratorAuditLogs />
    );
}


// =====================================================
// ADMINISTRATOR AUDIT DIRECTORY
// =====================================================

function AdministratorAuditLogs() {
    const [
        logs,
        setLogs,
    ] =
        useState<AuditLogItem[]>(
            [],
        );

    const [
        metadata,
        setMetadata,
    ] =
        useState<AuditLogMetadata>({
            actions: [],
            outcomes: [],
            resource_types: [],
        });

    const [
        total,
        setTotal,
    ] =
        useState(0);

    const [
        offset,
        setOffset,
    ] =
        useState(0);

    const [
        search,
        setSearch,
    ] =
        useState('');

    const [
        actionFilter,
        setActionFilter,
    ] =
        useState('');

    const [
        outcomeFilter,
        setOutcomeFilter,
    ] =
        useState('');

    const [
        resourceFilter,
        setResourceFilter,
    ] =
        useState('');

    const [
        dateFrom,
        setDateFrom,
    ] =
        useState('');

    const [
        dateTo,
        setDateTo,
    ] =
        useState('');

    const [
        selected,
        setSelected,
    ] =
        useState<
            AuditLogItem | null
        >(
            null,
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
    // LOAD FILTER METADATA
    // ===================================================

    useEffect(
        () => {
            api.auditLogMetadata()
                .then(
                    setMetadata,
                )
                .catch(
                    () => {
                        // Filtering can still work without metadata.
                    },
                );
        },
        [],
    );


    // ===================================================
    // LOAD AUDIT EVENTS
    // ===================================================

    useEffect(
        () => {
            let active =
                true;

            async function load() {
                setLoading(
                    true,
                );

                setError('');

                try {
                    const response =
                        await api.auditLogs({
                            search:
                                search.trim()
                                || undefined,

                            action:
                                actionFilter
                                || undefined,

                            outcome:
                                outcomeFilter
                                || undefined,

                            resourceType:
                                resourceFilter
                                || undefined,

                            // HTML datetime-local omits a timezone.
                            // Convert into an ISO timestamp before
                            // transmitting to FastAPI.
                            dateFrom:
                                dateFrom
                                    ? new Date(
                                        dateFrom,
                                    ).toISOString()
                                    : undefined,

                            dateTo:
                                dateTo
                                    ? new Date(
                                        dateTo,
                                    ).toISOString()
                                    : undefined,

                            limit:
                                PAGE_SIZE,

                            offset,
                        });

                    if (!active) {
                        return;
                    }

                    setLogs(
                        response.items,
                    );

                    setTotal(
                        response.total,
                    );
                } catch (
                errorValue
                ) {
                    if (!active) {
                        return;
                    }

                    setError(
                        errorValue instanceof Error
                            ? errorValue.message
                            : 'Unable to load audit events.',
                    );
                } finally {
                    if (active) {
                        setLoading(
                            false,
                        );
                    }
                }
            }

            // Small debounce prevents a backend request for
            // every individual search keystroke.
            const timer =
                window.setTimeout(
                    () => {
                        void load();
                    },
                    250,
                );

            return () => {
                active = false;

                window.clearTimeout(
                    timer,
                );
            };
        },
        [
            search,
            actionFilter,
            outcomeFilter,
            resourceFilter,
            dateFrom,
            dateTo,
            offset,
        ],
    );


    // ===================================================
    // RESET PAGE WHEN FILTERS CHANGE
    // ===================================================

    useEffect(
        () => {
            setOffset(
                0,
            );
        },
        [
            search,
            actionFilter,
            outcomeFilter,
            resourceFilter,
            dateFrom,
            dateTo,
        ],
    );


    // ===================================================
    // SUMMARY METRICS
    //
    // These represent the current loaded page rather than
    // pretending to be global totals for each category.
    // ===================================================

    const pageSuccessCount =
        useMemo(
            () =>
                logs.filter(
                    (
                        log,
                    ) =>
                        log.outcome
                            .toUpperCase()
                        === 'SUCCESS',
                ).length,
            [
                logs,
            ],
        );

    const pageFailureCount =
        useMemo(
            () =>
                logs.filter(
                    (
                        log,
                    ) =>
                        log.outcome
                            .toUpperCase()
                        !== 'SUCCESS',
                ).length,
            [
                logs,
            ],
        );


    // ===================================================
    // PAGINATION
    // ===================================================

    const currentPage =
        Math.floor(
            offset
            /
            PAGE_SIZE,
        )
        + 1;

    const pageCount =
        Math.max(
            1,
            Math.ceil(
                total
                /
                PAGE_SIZE,
            ),
        );


    function clearFilters() {
        setSearch('');
        setActionFilter('');
        setOutcomeFilter('');
        setResourceFilter('');
        setDateFrom('');
        setDateTo('');
        setOffset(0);
    }


    return (
        <>
            <PageHeader
                eyebrow="Governance & assurance"
                title="Audit logs"
                description="Review immutable MEDISCOPE activity records, security events and privileged administrative actions."
            />


            {/* =================================================
          SUMMARY
          ================================================= */}

            <section className="audit-summary-grid">
                <div>
                    <div className="audit-summary-icon">
                        <Activity size={19} />
                    </div>

                    <span>
                        Matching events
                    </span>

                    <strong>
                        {total}
                    </strong>

                    <small>
                        Current search and filters
                    </small>
                </div>

                <div>
                    <div className="audit-summary-icon success">
                        <CheckCircle2 size={19} />
                    </div>

                    <span>
                        Successful
                    </span>

                    <strong>
                        {pageSuccessCount}
                    </strong>

                    <small>
                        On this page
                    </small>
                </div>

                <div>
                    <div className="audit-summary-icon warning">
                        <AlertTriangle size={19} />
                    </div>

                    <span>
                        Other outcomes
                    </span>

                    <strong>
                        {pageFailureCount}
                    </strong>

                    <small>
                        On this page
                    </small>
                </div>

                <div>
                    <div className="audit-summary-icon security">
                        <ShieldCheck size={19} />
                    </div>

                    <span>
                        Audit policy
                    </span>

                    <strong>
                        Read only
                    </strong>

                    <small>
                        Historical records preserved
                    </small>
                </div>
            </section>


            {/* =================================================
          AUDIT DIRECTORY
          ================================================= */}

            <section className="audit-directory">
                <header className="audit-directory-header">
                    <div>
                        <span className="eyebrow">
                            Activity directory
                        </span>

                        <h2>
                            System events
                        </h2>

                        <p>
                            Newest events appear first.
                        </p>
                    </div>

                    <button
                        type="button"
                        className="button secondary small"
                        onClick={
                            clearFilters
                        }
                    >
                        <Filter size={15} />

                        Clear filters
                    </button>
                </header>


                {/* -----------------------------------------------
            SEARCH & PRIMARY FILTERS
            ----------------------------------------------- */}

                <div className="audit-toolbar">
                    <div className="audit-search">
                        <Search size={17} />

                        <input
                            type="search"
                            placeholder="Search action, actor, outcome or resource"
                            value={search}
                            onChange={
                                (
                                    event,
                                ) =>
                                    setSearch(
                                        event.target.value,
                                    )
                            }
                        />
                    </div>

                    <select
                        value={
                            outcomeFilter
                        }
                        onChange={
                            (
                                event,
                            ) =>
                                setOutcomeFilter(
                                    event.target.value,
                                )
                        }
                    >
                        <option value="">
                            All outcomes
                        </option>

                        {
                            metadata.outcomes.map(
                                (
                                    outcome,
                                ) => (
                                    <option
                                        key={
                                            outcome
                                        }
                                        value={
                                            outcome
                                        }
                                    >
                                        {
                                            humaniseValue(
                                                outcome,
                                            )
                                        }
                                    </option>
                                ),
                            )
                        }
                    </select>

                    <select
                        value={
                            resourceFilter
                        }
                        onChange={
                            (
                                event,
                            ) =>
                                setResourceFilter(
                                    event.target.value,
                                )
                        }
                    >
                        <option value="">
                            All resources
                        </option>

                        {
                            metadata.resource_types.map(
                                (
                                    resource,
                                ) => (
                                    <option
                                        key={
                                            resource
                                        }
                                        value={
                                            resource
                                        }
                                    >
                                        {
                                            humaniseValue(
                                                resource,
                                            )
                                        }
                                    </option>
                                ),
                            )
                        }
                    </select>
                </div>


                {/* -----------------------------------------------
            ADVANCED FILTERS
            ----------------------------------------------- */}

                <div className="audit-secondary-filters">
                    <label>
                        Action

                        <select
                            value={
                                actionFilter
                            }
                            onChange={
                                (
                                    event,
                                ) =>
                                    setActionFilter(
                                        event.target.value,
                                    )
                            }
                        >
                            <option value="">
                                All actions
                            </option>

                            {
                                metadata.actions.map(
                                    (
                                        action,
                                    ) => (
                                        <option
                                            key={
                                                action
                                            }
                                            value={
                                                action
                                            }
                                        >
                                            {
                                                humaniseValue(
                                                    action,
                                                )
                                            }
                                        </option>
                                    ),
                                )
                            }
                        </select>
                    </label>

                    <label>
                        From

                        <input
                            type="datetime-local"
                            value={
                                dateFrom
                            }
                            onChange={
                                (
                                    event,
                                ) =>
                                    setDateFrom(
                                        event.target.value,
                                    )
                            }
                        />
                    </label>

                    <label>
                        To

                        <input
                            type="datetime-local"
                            value={
                                dateTo
                            }
                            onChange={
                                (
                                    event,
                                ) =>
                                    setDateTo(
                                        event.target.value,
                                    )
                            }
                        />
                    </label>
                </div>


                {error && (
                    <div className="form-error audit-error">
                        {error}
                    </div>
                )}


                {/* -----------------------------------------------
            TABLE
            ----------------------------------------------- */}

                <div className="audit-table-wrapper">
                    <div className="audit-table">
                        <div className="audit-table-row header">
                            <span>
                                Time
                            </span>

                            <span>
                                Actor
                            </span>

                            <span>
                                Action
                            </span>

                            <span>
                                Resource
                            </span>

                            <span>
                                Outcome
                            </span>

                            <span />
                        </div>


                        {loading && (
                            <div className="audit-empty">
                                Loading audit events…
                            </div>
                        )}


                        {!loading &&
                            logs.length === 0 && (
                                <div className="audit-empty">
                                    No audit events match the current filters.
                                </div>
                            )}


                        {!loading &&
                            logs.map(
                                (
                                    log,
                                ) => (
                                    <button
                                        type="button"
                                        className="audit-table-row audit-event-row"
                                        key={
                                            log.id
                                        }
                                        onClick={
                                            () =>
                                                setSelected(
                                                    log,
                                                )
                                        }
                                    >
                                        <time>
                                            {
                                                formatAuditDate(
                                                    log.created_at,
                                                )
                                            }
                                        </time>

                                        <div className="audit-actor">
                                            <strong>
                                                {
                                                    log.actor_name
                                                    ?? 'System'
                                                }
                                            </strong>

                                            <span>
                                                {
                                                    log.actor_email
                                                    ?? (
                                                        log.actor_user_id
                                                        ?? 'System event'
                                                    )
                                                }
                                            </span>
                                        </div>

                                        <span className="audit-action">
                                            {
                                                humaniseValue(
                                                    log.action,
                                                )
                                            }
                                        </span>

                                        <div className="audit-resource">
                                            <strong>
                                                {
                                                    log.resource_type
                                                        ? humaniseValue(
                                                            log.resource_type,
                                                        )
                                                        : '—'
                                                }
                                            </strong>

                                            <span>
                                                {
                                                    log.resource_id
                                                    ?? ''
                                                }
                                            </span>
                                        </div>

                                        <span
                                            className="audit-outcome"
                                            data-outcome={
                                                log.outcome
                                                    .toUpperCase()
                                            }
                                        >
                                            {
                                                humaniseValue(
                                                    log.outcome,
                                                )
                                            }
                                        </span>

                                        <ChevronRight
                                            size={16}
                                        />
                                    </button>
                                ),
                            )}
                    </div>
                </div>


                {/* -----------------------------------------------
            PAGINATION
            ----------------------------------------------- */}

                <footer className="audit-pagination">
                    <span>
                        Page {currentPage} of {pageCount}
                        {' · '}
                        {total} event{
                            total === 1
                                ? ''
                                : 's'
                        }
                    </span>

                    <div>
                        <button
                            type="button"
                            className="button secondary small"
                            disabled={
                                offset === 0
                                ||
                                loading
                            }
                            onClick={
                                () =>
                                    setOffset(
                                        Math.max(
                                            0,
                                            offset
                                            - PAGE_SIZE,
                                        ),
                                    )
                            }
                        >
                            Previous
                        </button>

                        <button
                            type="button"
                            className="button secondary small"
                            disabled={
                                offset
                                + PAGE_SIZE
                                >= total
                                ||
                                loading
                            }
                            onClick={
                                () =>
                                    setOffset(
                                        offset
                                        + PAGE_SIZE,
                                    )
                            }
                        >
                            Next
                        </button>
                    </div>
                </footer>
            </section>


            {/* =================================================
          EVENT DETAIL DRAWER
          ================================================= */}

            {selected && (
                <div
                    className="audit-drawer-backdrop"
                    onMouseDown={
                        (
                            event,
                        ) => {
                            if (
                                event.target
                                === event.currentTarget
                            ) {
                                setSelected(
                                    null,
                                );
                            }
                        }
                    }
                >
                    <aside className="audit-drawer">
                        <header className="audit-drawer-header">
                            <div>
                                <span className="eyebrow">
                                    Audit event
                                </span>

                                <h2>
                                    {
                                        humaniseValue(
                                            selected.action,
                                        )
                                    }
                                </h2>

                                <p>
                                    {
                                        formatAuditDate(
                                            selected.created_at,
                                        )
                                    }
                                </p>
                            </div>

                            <button
                                type="button"
                                className="icon-button"
                                aria-label="Close audit event"
                                onClick={
                                    () =>
                                        setSelected(
                                            null,
                                        )
                                }
                            >
                                <X size={18} />
                            </button>
                        </header>


                        <div className="audit-drawer-content">

                            <div className="audit-event-highlight">
                                {
                                    selected.outcome
                                        .toUpperCase()
                                        === 'SUCCESS'
                                        ? (
                                            <CheckCircle2 size={22} />
                                        )
                                        : (
                                            <AlertTriangle size={22} />
                                        )
                                }

                                <div>
                                    <span>
                                        Outcome
                                    </span>

                                    <strong>
                                        {
                                            humaniseValue(
                                                selected.outcome,
                                            )
                                        }
                                    </strong>
                                </div>
                            </div>


                            <div className="audit-detail-grid">
                                <div>
                                    <span>
                                        Actor
                                    </span>

                                    <strong>
                                        {
                                            selected.actor_name
                                            ?? 'System'
                                        }
                                    </strong>
                                </div>

                                <div>
                                    <span>
                                        Actor email
                                    </span>

                                    <strong>
                                        {
                                            selected.actor_email
                                            ?? 'Not applicable'
                                        }
                                    </strong>
                                </div>

                                <div>
                                    <span>
                                        Actor user ID
                                    </span>

                                    <strong>
                                        {
                                            selected.actor_user_id
                                            ?? 'System'
                                        }
                                    </strong>
                                </div>

                                <div>
                                    <span>
                                        Action
                                    </span>

                                    <strong>
                                        {selected.action}
                                    </strong>
                                </div>

                                <div>
                                    <span>
                                        Resource
                                    </span>

                                    <strong>
                                        {
                                            selected.resource_type
                                            ?? 'Not specified'
                                        }
                                    </strong>
                                </div>

                                <div>
                                    <span>
                                        Resource ID
                                    </span>

                                    <strong>
                                        {
                                            selected.resource_id
                                            ?? 'Not specified'
                                        }
                                    </strong>
                                </div>

                                <div>
                                    <span>
                                        IP address
                                    </span>

                                    <strong>
                                        {
                                            selected.ip_address
                                            ?? 'Not recorded'
                                        }
                                    </strong>
                                </div>

                                <div>
                                    <span>
                                        Timestamp
                                    </span>

                                    <strong>
                                        {
                                            formatAuditDate(
                                                selected.created_at,
                                            )
                                        }
                                    </strong>
                                </div>
                            </div>


                            <section className="audit-detail-section">
                                <div className="audit-detail-heading">
                                    <Globe2 size={17} />

                                    <h3>
                                        Client information
                                    </h3>
                                </div>

                                <p>
                                    {
                                        selected.user_agent
                                        ?? 'No user-agent information was recorded.'
                                    }
                                </p>
                            </section>


                            <section className="audit-detail-section">
                                <div className="audit-detail-heading">
                                    <Activity size={17} />

                                    <h3>
                                        Event details
                                    </h3>
                                </div>

                                {
                                    selected.details
                                        &&
                                        Object.keys(
                                            selected.details,
                                        ).length > 0
                                        ? (
                                            <div className="audit-json-details">
                                                {
                                                    Object.entries(
                                                        selected.details,
                                                    ).map(
                                                        (
                                                            [
                                                                key,
                                                                value,
                                                            ],
                                                        ) => (
                                                            <div
                                                                key={
                                                                    key
                                                                }
                                                            >
                                                                <span>
                                                                    {
                                                                        humaniseValue(
                                                                            key,
                                                                        )
                                                                    }
                                                                </span>

                                                                <strong>
                                                                    {
                                                                        typeof value
                                                                            === 'object'
                                                                            ? JSON.stringify(
                                                                                value,
                                                                            )
                                                                            : String(
                                                                                value,
                                                                            )
                                                                    }
                                                                </strong>
                                                            </div>
                                                        ),
                                                    )
                                                }
                                            </div>
                                        )
                                        : (
                                            <p>
                                                No additional event metadata was recorded.
                                            </p>
                                        )
                                }
                            </section>


                            <div className="audit-readonly-notice">
                                <ShieldCheck size={17} />

                                <div>
                                    <strong>
                                        Read-only audit record
                                    </strong>

                                    <span>
                                        MEDISCOPE does not permit administrators
                                        to modify or delete audit events from this
                                        interface.
                                    </span>
                                </div>
                            </div>
                        </div>
                    </aside>
                </div>
            )}
        </>
    );
}
