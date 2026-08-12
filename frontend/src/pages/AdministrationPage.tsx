import {
    Activity,
    ArrowDownAZ,
    CheckCircle2,
    ChevronDown,
    ChevronRight,
    CircleUserRound,
    Filter,
    Link2,
    Mail,
    MoreHorizontal,
    Search,
    ShieldCheck,
    Stethoscope,
    Trash2,
    Unlink,
    UserCheck,
    UserCog,
    UserPlus,
    Users,
    X,
} from 'lucide-react';

import {
    useEffect,
    useMemo,
    useState,
    type FormEvent,
} from 'react';

import {
    useSearchParams,
} from 'react-router-dom';

import {
    PageHeader,
} from '../components/UI';

import {
    PasswordInput,
} from '../components/PasswordInput';

import {
    useAuth,
} from '../context/AuthContext';

import {
    api,
} from '../lib/api';

import type {
    AdministrationMetadata,
    AdminPatientSummary,
    ClinicianAssignment,
    Role,
    UserProfile,
} from '../lib/types';


// =====================================================
// ADMINISTRATION TYPES
// =====================================================

type AccountFilter =
    | 'ALL'
    | Role;

type SortOption =
    | 'NAME_ASC'
    | 'NAME_DESC'
    | 'ROLE'
    | 'STATUS';

type DrawerMode =
    | 'CREATE'
    | 'EDIT'
    | 'GOVERNANCE'
    | 'CLINICIAN_ASSIGNMENTS'
    | 'USER_RELATIONSHIPS'
    | null;


type CreateUserForm = {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    date_of_birth: string;
    phone: string;
    gender: string;
    role: Role;
};


type EditUserForm = {
    first_name: string;
    last_name: string;
    date_of_birth: string;
    phone: string;
    gender: string;
};


// =====================================================
// PRESENTATION HELPERS
// =====================================================

function roleLabel(
    role: string,
): string {
    switch (role) {
        case 'ADMINISTRATOR':
            return 'Administrator';

        case 'CLINICIAN':
            return 'Clinician';

        case 'USER':
            return 'Standard user';

        default:
            return role;
    }
}


function accountStatusLabel(
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


function patientLabel(
    patient: AdminPatientSummary,
): string {
    const name =
        [
            patient.first_name,
            patient.last_name,
        ]
            .filter(Boolean)
            .join(' ');

    return name
        ? `${patient.synthetic_patient_number} · ${name}`
        : patient.synthetic_patient_number;
}


// =====================================================
// ADMINISTRATION PAGE
// =====================================================

export default function AdministrationPage() {
    const {
        user: currentAdmin,
    } =
        useAuth();

    const [
        searchParams,
        setSearchParams,
    ] =
        useSearchParams();


    // ===================================================
    // GLOBAL CLINICAL ASSIGNMENT WORKSPACE
    //
    // This state belongs to the system-wide assignment
    // manager displayed below the account directory.
    // It is intentionally separate from the per-user
    // relationship drawer state.
    // ===================================================

    const [
        assignmentClinicianId,
        setAssignmentClinicianId,
    ] =
        useState('');

    const [
        selectedAssignmentPatientIds,
        setSelectedAssignmentPatientIds,
    ] =
        useState<string[]>(
            [],
        );

    const [
        assignmentPatientSearch,
        setAssignmentPatientSearch,
    ] =
        useState('');

    const [
        assignmentClinicianFilter,
        setAssignmentClinicianFilter,
    ] =
        useState('ALL');

    const [
        assignmentBusy,
        setAssignmentBusy,
    ] =
        useState(false);


    // ===================================================
    // DIRECTORY STATE
    // ===================================================

    const [
        users,
        setUsers,
    ] =
        useState<UserProfile[]>(
            [],
        );

    const [
        patients,
        setPatients,
    ] =
        useState<
            AdminPatientSummary[]
        >(
            [],
        );

    const [
        assignments,
        setAssignments,
    ] =
        useState<
            ClinicianAssignment[]
        >(
            [],
        );

    const [
        metadata,
        setMetadata,
    ] =
        useState<
            AdministrationMetadata | null
        >(
            null,
        );


    // ===================================================
    // FILTER STATE
    // ===================================================

    const initialRole =
        searchParams.get(
            'role',
        );

    const [
        filter,
        setFilter,
    ] =
        useState<AccountFilter>(
            initialRole === 'USER'
                ||
                initialRole === 'CLINICIAN'
                ||
                initialRole === 'ADMINISTRATOR'
                ? initialRole
                : 'ALL',
        );

    const [
        search,
        setSearch,
    ] =
        useState('');

    const [
        sort,
        setSort,
    ] =
        useState<SortOption>(
            'NAME_ASC',
        );

    const [
        expandedUserId,
        setExpandedUserId,
    ] =
        useState<
            string | null
        >(
            null,
        );


    // ===================================================
    // DRAWER STATE
    // ===================================================

    const [
        drawerMode,
        setDrawerMode,
    ] =
        useState<DrawerMode>(
            null,
        );

    const [
        selectedUser,
        setSelectedUser,
    ] =
        useState<
            UserProfile | null
        >(
            null,
        );


    // ===================================================
    // FORMS
    // ===================================================

    const [
        createForm,
        setCreateForm,
    ] =
        useState<CreateUserForm>({
            email: '',
            password: '',
            first_name: '',
            last_name: '',
            date_of_birth: '',
            phone: '',
            gender: '',
            role: 'USER',
        });

    const [
        editForm,
        setEditForm,
    ] =
        useState<EditUserForm>({
            first_name: '',
            last_name: '',
            date_of_birth: '',
            phone: '',
            gender: '',
        });

    const [
        governanceRole,
        setGovernanceRole,
    ] =
        useState<Role>(
            'USER',
        );

    const [
        governanceStatus,
        setGovernanceStatus,
    ] =
        useState('');

    const [
        patientSelection,
        setPatientSelection,
    ] =
        useState('');


    // ===================================================
    // UX STATE
    // ===================================================

    const [
        loading,
        setLoading,
    ] =
        useState(true);

    const [
        actionBusy,
        setActionBusy,
    ] =
        useState(false);

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


    // ===================================================
    // LOAD / REFRESH ADMINISTRATION DATA
    // ===================================================

    async function loadAdministration() {
        setLoading(
            true,
        );

        setError('');

        try {
            const [
                userResult,
                patientResult,
                assignmentResult,
                metadataResult,
            ] =
                await Promise.all([
                    api.adminUsers(),
                    api.adminPatients(),
                    api.adminAssignments({
                        activeOnly: true,
                    }),
                    api.adminMetadata(),
                ]);

            setUsers(
                userResult,
            );

            setPatients(
                patientResult,
            );

            setAssignments(
                assignmentResult,
            );

            setMetadata(
                metadataResult,
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to load administration data.',
            );
        } finally {
            setLoading(
                false,
            );
        }
    }


    useEffect(
        () => {
            void loadAdministration();
        },
        [],
    );


    // ===================================================
    // COUNTS
    // ===================================================

    const administrators =
        users.filter(
            (
                account,
            ) =>
                account.role
                === 'ADMINISTRATOR',
        );

    const clinicians =
        users.filter(
            (
                account,
            ) =>
                account.role
                === 'CLINICIAN',
        );

    const standardUsers =
        users.filter(
            (
                account,
            ) =>
                account.role
                === 'USER',
        );

    const activeUsers =
        users.filter(
            (
                account,
            ) =>
                account.account_status
                === 'ACTIVE',
        );


    // ===================================================
    // FILTER / SEARCH / SORT
    // ===================================================

    const visibleUsers =
        useMemo(
            () => {
                let result =
                    [...users];

                if (
                    filter !== 'ALL'
                ) {
                    result =
                        result.filter(
                            (
                                account,
                            ) =>
                                account.role
                                === filter,
                        );
                }

                const query =
                    search
                        .trim()
                        .toLowerCase();

                if (query) {
                    result =
                        result.filter(
                            (
                                account,
                            ) =>
                                [
                                    account.first_name,
                                    account.last_name,
                                    account.email,
                                    account.role,
                                    account.account_status,
                                ]
                                    .filter(Boolean)
                                    .join(' ')
                                    .toLowerCase()
                                    .includes(
                                        query,
                                    ),
                        );
                }

                result.sort(
                    (
                        first,
                        second,
                    ) => {
                        const firstName =
                            `${first.first_name} ${first.last_name}`;

                        const secondName =
                            `${second.first_name} ${second.last_name}`;

                        switch (sort) {
                            case 'NAME_DESC':
                                return secondName.localeCompare(
                                    firstName,
                                );

                            case 'ROLE':
                                return first.role.localeCompare(
                                    second.role,
                                );

                            case 'STATUS':
                                return first.account_status.localeCompare(
                                    second.account_status,
                                );

                            case 'NAME_ASC':
                            default:
                                return firstName.localeCompare(
                                    secondName,
                                );
                        }
                    },
                );

                return result;
            },
            [
                users,
                filter,
                search,
                sort,
            ],
        );


    // ===================================================
    // RELATIONSHIP HELPERS
    // ===================================================

    function linkedPatientForUser(
        userId: string,
    ) {
        return patients.find(
            (
                patient,
            ) =>
                patient.linked_user_id
                === userId,
        );
    }


    function assignmentsForClinician(
        clinicianId: string,
    ) {
        return assignments.filter(
            (
                assignment,
            ) =>
                assignment.clinician_user_id
                === clinicianId
                &&
                assignment.is_active,
        );
    }


    function assignmentsForPatient(
        patientId: string,
    ) {
        return assignments.filter(
            (
                assignment,
            ) =>
                assignment.patient_id
                === patientId
                &&
                assignment.is_active,
        );
    }


    function patientById(
        patientId: string,
    ) {
        return patients.find(
            (
                patient,
            ) =>
                patient.id
                === patientId,
        );
    }


    function clinicianById(
        clinicianId: string,
    ) {
        return users.find(
            (
                account,
            ) =>
                account.id
                === clinicianId,
        );
    }


    // ===================================================
    // GLOBAL ASSIGNMENT WORKSPACE HELPERS
    // ===================================================

    /**
     * Return patient IDs already assigned to the clinician
     * currently selected in the global assignment workspace.
     *
     * These patients are removed from the "available" list so
     * the administrator cannot accidentally request a duplicate
     * active assignment from the UI.
     *
     * The backend still remains authoritative and independently
     * prevents duplicate active assignments.
     */
    const selectedClinicianPatientIds =
        useMemo(
            () => {
                if (
                    !assignmentClinicianId
                ) {
                    return new Set<
                        string
                    >();
                }

                return new Set(
                    assignments
                        .filter(
                            (
                                assignment,
                            ) =>
                                assignment.is_active
                                &&
                                assignment.clinician_user_id
                                === assignmentClinicianId,
                        )
                        .map(
                            (
                                assignment,
                            ) =>
                                assignment.patient_id,
                        ),
                );
            },
            [
                assignments,
                assignmentClinicianId,
            ],
        );


    /**
     * Patients available for a new assignment.
     *
     * A patient may legitimately have more than one clinician,
     * therefore we only remove patients already assigned to the
     * currently selected clinician.
     */
    const availableAssignmentPatients =
        useMemo(
            () => {
                const query =
                    assignmentPatientSearch
                        .trim()
                        .toLowerCase();

                return patients.filter(
                    (
                        patient,
                    ) => {
                        if (
                            selectedClinicianPatientIds.has(
                                patient.id,
                            )
                        ) {
                            return false;
                        }

                        if (!query) {
                            return true;
                        }

                        return [
                            patient.synthetic_patient_number,
                            patient.first_name,
                            patient.last_name,
                            patient.state,
                            patient.lga,
                        ]
                            .filter(Boolean)
                            .join(' ')
                            .toLowerCase()
                            .includes(
                                query,
                            );
                    },
                );
            },
            [
                patients,
                assignmentPatientSearch,
                selectedClinicianPatientIds,
            ],
        );


    /**
     * Prepare assignment rows for the global relationship
     * table. Missing patient or clinician data is tolerated so
     * historical identifiers can still be represented safely.
     */
    const globalAssignmentRows =
        useMemo(
            () =>
                assignments
                    .filter(
                        (
                            assignment,
                        ) =>
                            assignment.is_active,
                    )
                    .map(
                        (
                            assignment,
                        ) => ({
                            assignment,

                            clinician:
                                clinicianById(
                                    assignment.clinician_user_id,
                                ),

                            patient:
                                patientById(
                                    assignment.patient_id,
                                ),
                        }),
                    )
                    .filter(
                        (
                            row,
                        ) =>
                            assignmentClinicianFilter
                            === 'ALL'
                            ||
                            row.assignment.clinician_user_id
                            === assignmentClinicianFilter,
                    ),
            [
                assignments,
                users,
                patients,
                assignmentClinicianFilter,
            ],
        );


    const assignedClinicianCount =
        new Set(
            assignments
                .filter(
                    (
                        assignment,
                    ) =>
                        assignment.is_active,
                )
                .map(
                    (
                        assignment,
                    ) =>
                        assignment.clinician_user_id,
                ),
        ).size;


    const assignedPatientCount =
        new Set(
            assignments
                .filter(
                    (
                        assignment,
                    ) =>
                        assignment.is_active,
                )
                .map(
                    (
                        assignment,
                    ) =>
                        assignment.patient_id,
                ),
        ).size;


    const unassignedPatientCount =
        patients.filter(
            (
                patient,
            ) =>
                !assignments.some(
                    (
                        assignment,
                    ) =>
                        assignment.is_active
                        &&
                        assignment.patient_id
                        === patient.id,
                ),
        ).length;


    // ===================================================
    // FILTER HANDLER
    // ===================================================

    function selectFilter(
        nextFilter:
            AccountFilter,
    ) {
        setFilter(
            nextFilter,
        );

        setExpandedUserId(
            null,
        );

        if (
            nextFilter
            === 'ALL'
        ) {
            setSearchParams(
                {},
            );
        } else {
            setSearchParams({
                role:
                    nextFilter,
            });
        }
    }


    // ===================================================
    // DRAWER HELPERS
    // ===================================================

    function closeDrawer() {
        setDrawerMode(
            null,
        );

        setSelectedUser(
            null,
        );

        setPatientSelection(
            '',
        );

        setError('');
    }


    function openCreateDrawer() {
        setSelectedUser(
            null,
        );

        setCreateForm({
            email: '',
            password: '',
            first_name: '',
            last_name: '',
            date_of_birth: '',
            phone: '',
            gender: '',
            role: 'USER',
        });

        setError('');
        setMessage('');

        setDrawerMode(
            'CREATE',
        );
    }


    function openEditDrawer(
        account:
            UserProfile,
    ) {
        setSelectedUser(
            account,
        );

        setEditForm({
            first_name:
                account.first_name,

            last_name:
                account.last_name,

            date_of_birth:
                account.date_of_birth
                ?? '',

            phone:
                account.phone
                ?? '',

            gender:
                account.gender
                ?? '',
        });

        setError('');
        setMessage('');

        setDrawerMode(
            'EDIT',
        );
    }


    function openGovernanceDrawer(
        account:
            UserProfile,
    ) {
        setSelectedUser(
            account,
        );

        setGovernanceRole(
            account.role,
        );

        setGovernanceStatus(
            account.account_status,
        );

        setError('');
        setMessage('');

        setDrawerMode(
            'GOVERNANCE',
        );
    }


    function openClinicianAssignments(
        account:
            UserProfile,
    ) {
        setSelectedUser(
            account,
        );

        setPatientSelection(
            '',
        );

        setError('');
        setMessage('');

        setDrawerMode(
            'CLINICIAN_ASSIGNMENTS',
        );
    }


    function openUserRelationships(
        account:
            UserProfile,
    ) {
        setSelectedUser(
            account,
        );

        setPatientSelection(
            '',
        );

        setError('');
        setMessage('');

        setDrawerMode(
            'USER_RELATIONSHIPS',
        );
    }


    // ===================================================
    // CREATE USER
    // ===================================================

    async function createAccount(
        event:
            FormEvent,
    ) {
        event.preventDefault();

        setActionBusy(
            true,
        );

        setError('');
        setMessage('');

        try {
            await api.adminCreateUser({
                email:
                    createForm.email
                        .trim()
                        .toLowerCase(),

                password:
                    createForm.password,

                first_name:
                    createForm.first_name
                        .trim(),

                last_name:
                    createForm.last_name
                        .trim(),

                date_of_birth:
                    createForm.date_of_birth
                    || null,

                phone:
                    createForm.phone.trim()
                    || null,

                gender:
                    createForm.gender
                    || null,

                role:
                    createForm.role,
            });

            await loadAdministration();

            closeDrawer();

            setMessage(
                'Account created successfully.',
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to create account.',
            );
        } finally {
            setActionBusy(
                false,
            );
        }
    }


    // ===================================================
    // EDIT USER
    // ===================================================

    async function updateAccount(
        event:
            FormEvent,
    ) {
        event.preventDefault();

        if (!selectedUser) {
            return;
        }

        setActionBusy(
            true,
        );

        setError('');
        setMessage('');

        try {
            await api.adminUpdateUser(
                selectedUser.id,
                {
                    first_name:
                        editForm.first_name.trim(),

                    last_name:
                        editForm.last_name.trim(),

                    date_of_birth:
                        editForm.date_of_birth
                        || null,

                    phone:
                        editForm.phone.trim()
                        || null,

                    gender:
                        editForm.gender
                        || null,
                },
            );

            await loadAdministration();

            closeDrawer();

            setMessage(
                'Account details updated successfully.',
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to update account.',
            );
        } finally {
            setActionBusy(
                false,
            );
        }
    }


    // ===================================================
    // ROLE / STATUS GOVERNANCE
    // ===================================================

    async function saveGovernance() {
        if (!selectedUser) {
            return;
        }

        setActionBusy(
            true,
        );

        setError('');
        setMessage('');

        try {
            if (
                governanceRole
                !== selectedUser.role
            ) {
                await api.adminChangeUserRole(
                    selectedUser.id,
                    governanceRole,
                );
            }

            if (
                governanceStatus
                !== selectedUser.account_status
            ) {
                await api.adminChangeUserStatus(
                    selectedUser.id,
                    governanceStatus,
                );
            }

            await loadAdministration();

            closeDrawer();

            setMessage(
                'Account governance settings updated.',
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to update account governance.',
            );
        } finally {
            setActionBusy(
                false,
            );
        }
    }


    // ===================================================
    // SOFT DELETE USER
    // ===================================================

    async function deleteAccount() {
        if (!selectedUser) {
            return;
        }

        const confirmed =
            window.confirm(
                `Soft-delete ${selectedUser.first_name} ${selectedUser.last_name}? Historical records will be preserved.`,
            );

        if (!confirmed) {
            return;
        }

        setActionBusy(
            true,
        );

        setError('');

        try {
            await api.adminDeleteUser(
                selectedUser.id,
            );

            await loadAdministration();

            closeDrawer();

            setMessage(
                'Account removed successfully.',
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to remove account.',
            );
        } finally {
            setActionBusy(
                false,
            );
        }
    }


    // ===================================================
    // CLINICIAN → PATIENT ASSIGNMENT
    // ===================================================

    async function assignSelectedPatient() {
        if (
            !selectedUser
            ||
            !patientSelection
        ) {
            return;
        }

        setActionBusy(
            true,
        );

        setError('');

        try {
            await api.adminAssignClinician(
                selectedUser.id,
                patientSelection,
            );

            await loadAdministration();

            setPatientSelection(
                '',
            );

            setMessage(
                'Patient assigned successfully.',
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to assign patient.',
            );
        } finally {
            setActionBusy(
                false,
            );
        }
    }


    async function endClinicianAssignment(
        assignmentId:
            string,
    ) {
        const confirmed =
            window.confirm(
                'End this clinician-patient assignment?',
            );

        if (!confirmed) {
            return;
        }

        setActionBusy(
            true,
        );

        setError('');

        try {
            await api.adminEndAssignment(
                assignmentId,
            );

            await loadAdministration();

            setMessage(
                'Assignment ended successfully.',
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to end assignment.',
            );
        } finally {
            setActionBusy(
                false,
            );
        }
    }


    // ===================================================
    // USER ↔ PATIENT LINK
    // ===================================================

    async function linkSelectedPatient() {
        if (
            !selectedUser
            ||
            !patientSelection
        ) {
            return;
        }

        setActionBusy(
            true,
        );

        setError('');

        try {
            await api.adminLinkUserToPatient(
                patientSelection,
                selectedUser.id,
            );

            await loadAdministration();

            setPatientSelection(
                '',
            );

            setMessage(
                'User linked to patient successfully.',
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to link patient.',
            );
        } finally {
            setActionBusy(
                false,
            );
        }
    }


    async function unlinkPatient(
        patientId:
            string,
    ) {
        const confirmed =
            window.confirm(
                'Remove the user-account link from this patient profile?',
            );

        if (!confirmed) {
            return;
        }

        setActionBusy(
            true,
        );

        setError('');

        try {
            await api.adminUnlinkUserFromPatient(
                patientId,
            );

            await loadAdministration();

            setMessage(
                'Patient account link removed.',
            );
        } catch (
        errorValue
        ) {
            setError(
                errorValue instanceof Error
                    ? errorValue.message
                    : 'Unable to unlink patient.',
            );
        } finally {
            setActionBusy(
                false,
            );
        }
    }


    // ===================================================
    // MULTI-PATIENT SELECTION
    // ===================================================

    function toggleAssignmentPatient(
        patientId:
            string,
    ) {
        setSelectedAssignmentPatientIds(
            (
                current,
            ) =>
                current.includes(
                    patientId,
                )
                    ? current.filter(
                        (
                            id,
                        ) =>
                            id !== patientId,
                    )
                    : [
                        ...current,
                        patientId,
                    ],
        );
    }


    // ===================================================
    // GLOBAL MULTI-PATIENT ASSIGNMENT
    // ===================================================

    async function assignSelectedPatients() {
        if (
            !assignmentClinicianId
            ||
            selectedAssignmentPatientIds.length
            === 0
        ) {
            return;
        }

        setAssignmentBusy(
            true,
        );

        setError('');
        setMessage('');

        let successCount =
            0;

        const failures:
            string[] = [];

        try {
            // Each relationship is its own database operation.
            // Processing individually allows MEDISCOPE to report
            // partial success rather than hiding successful
            // assignments if one relationship fails.
            for (
                const patientId
                of selectedAssignmentPatientIds
            ) {
                try {
                    await api.adminAssignClinician(
                        assignmentClinicianId,
                        patientId,
                    );

                    successCount += 1;
                } catch (
                errorValue
                ) {
                    failures.push(
                        errorValue instanceof Error
                            ? errorValue.message
                            : 'An assignment could not be created.',
                    );
                }
            }

            await loadAdministration();

            setSelectedAssignmentPatientIds(
                [],
            );

            if (
                successCount > 0
            ) {
                setMessage(
                    `${successCount} patient${successCount === 1
                        ? ''
                        : 's'
                    } assigned successfully.`,
                );
            }

            if (
                failures.length > 0
            ) {
                setError(
                    `${failures.length
                    } assignment${failures.length === 1
                        ? ''
                        : 's'
                    } could not be completed. ${failures[0]}`,
                );
            }
        } finally {
            setAssignmentBusy(
                false,
            );
        }
    }


    // ===================================================
    // DERIVED DRAWER RELATIONSHIPS
    // ===================================================

    const selectedLinkedPatient =
        selectedUser
            ? linkedPatientForUser(
                selectedUser.id,
            )
            : undefined;

    const selectedClinicianAssignments =
        selectedUser
            ? assignmentsForClinician(
                selectedUser.id,
            )
            : [];

    const selectedPatientAssignments =
        selectedLinkedPatient
            ? assignmentsForPatient(
                selectedLinkedPatient.id,
            )
            : [];


    // ===================================================
    // RENDER
    // ===================================================

    return (
        <>
            <PageHeader
                eyebrow="Administration"
                title="Identity & access control"
                description="Manage MEDISCOPE accounts, roles, workforce access, patient relationships and administrative governance."
            />


            {/* =================================================
          PAGE FEEDBACK
          ================================================= */}

            {message && (
                <div className="form-info admin-page-message">
                    <CheckCircle2 size={17} />

                    {message}
                </div>
            )}

            {error && !drawerMode && (
                <div className="form-error admin-page-message">
                    {error}
                </div>
            )}


            {/* =================================================
          KPI FILTERS
          ================================================= */}

            <section className="admin-kpi-grid">
                <button
                    type="button"
                    className={
                        filter === 'ALL'
                            ? 'admin-kpi-card active'
                            : 'admin-kpi-card'
                    }
                    onClick={
                        () =>
                            selectFilter(
                                'ALL',
                            )
                    }
                >
                    <div className="admin-kpi-icon all">
                        <Users size={21} />
                    </div>

                    <div>
                        <span>
                            All accounts
                        </span>

                        <strong>
                            {users.length}
                        </strong>

                        <small>
                            Entire directory
                        </small>
                    </div>
                </button>


                <button
                    type="button"
                    className={
                        filter === 'CLINICIAN'
                            ? 'admin-kpi-card active'
                            : 'admin-kpi-card'
                    }
                    onClick={
                        () =>
                            selectFilter(
                                'CLINICIAN',
                            )
                    }
                >
                    <div className="admin-kpi-icon clinician">
                        <Stethoscope size={21} />
                    </div>

                    <div>
                        <span>
                            Clinicians
                        </span>

                        <strong>
                            {clinicians.length}
                        </strong>

                        <small>
                            Clinical workforce
                        </small>
                    </div>
                </button>


                <button
                    type="button"
                    className={
                        filter === 'USER'
                            ? 'admin-kpi-card active'
                            : 'admin-kpi-card'
                    }
                    onClick={
                        () =>
                            selectFilter(
                                'USER',
                            )
                    }
                >
                    <div className="admin-kpi-icon users">
                        <CircleUserRound size={21} />
                    </div>

                    <div>
                        <span>
                            Standard users
                        </span>

                        <strong>
                            {standardUsers.length}
                        </strong>

                        <small>
                            Patient-facing accounts
                        </small>
                    </div>
                </button>


                <button
                    type="button"
                    className={
                        filter === 'ADMINISTRATOR'
                            ? 'admin-kpi-card active'
                            : 'admin-kpi-card'
                    }
                    onClick={
                        () =>
                            selectFilter(
                                'ADMINISTRATOR',
                            )
                    }
                >
                    <div className="admin-kpi-icon administrator">
                        <ShieldCheck size={21} />
                    </div>

                    <div>
                        <span>
                            Administrators
                        </span>

                        <strong>
                            {administrators.length}
                        </strong>

                        <small>
                            Privileged accounts
                        </small>
                    </div>
                </button>
            </section>


            {/* =================================================
          HEALTH / GOVERNANCE STRIP
          ================================================= */}

            <section className="admin-health-strip">
                <div>
                    <UserCheck size={18} />

                    <span>
                        Active accounts
                    </span>

                    <strong>
                        {activeUsers.length}
                    </strong>
                </div>

                <div>
                    <ShieldCheck size={18} />

                    <span>
                        RBAC policy
                    </span>

                    <strong>
                        Enforced
                    </strong>
                </div>

                <div>
                    <Activity size={18} />

                    <span>
                        Active assignments
                    </span>

                    <strong>
                        {assignments.length}
                    </strong>
                </div>
            </section>


            {/* =================================================
          DIRECTORY
          ================================================= */}

            <section className="admin-directory">
                <header className="admin-directory-header">
                    <div>
                        <span className="eyebrow">
                            Account directory
                        </span>

                        <h2>
                            {
                                filter === 'ALL'
                                    ? 'All MEDISCOPE accounts'
                                    : `${roleLabel(filter)} accounts`
                            }
                        </h2>

                        <p>
                            {visibleUsers.length}{' '}
                            account{
                                visibleUsers.length === 1
                                    ? ''
                                    : 's'
                            } shown
                        </p>
                    </div>

                    <button
                        type="button"
                        className="button primary"
                        onClick={
                            openCreateDrawer
                        }
                    >
                        <UserPlus size={17} />

                        Create account
                    </button>
                </header>


                {/* -----------------------------------------------
            TOOLBAR
            ----------------------------------------------- */}

                <div className="admin-directory-toolbar">
                    <div className="admin-search">
                        <Search size={17} />

                        <input
                            type="search"
                            placeholder="Search name, email, role or status"
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

                    <div className="admin-filter-control">
                        <Filter size={16} />

                        <select
                            value={filter}
                            onChange={
                                (
                                    event,
                                ) =>
                                    selectFilter(event.target.value as AccountFilter,
                                    )
                            }
                        >
                            <option value="ALL">
                                All roles
                            </option>

                            <option value="ADMINISTRATOR">
                                Administrators
                            </option>

                            <option value="CLINICIAN">
                                Clinicians
                            </option>

                            <option value="USER">
                                Standard users
                            </option>
                        </select>
                    </div>

                    <div className="admin-filter-control">
                        <ArrowDownAZ size={16} />

                        <select
                            value={sort}
                            onChange={
                                (
                                    event,
                                ) =>
                                    setSort(
                                        event.target.value as SortOption,
                                    )
                            }
                        >
                            <option value="NAME_ASC">
                                Name A–Z
                            </option>

                            <option value="NAME_DESC">
                                Name Z–A
                            </option>

                            <option value="ROLE">
                                Role
                            </option>

                            <option value="STATUS">
                                Status
                            </option>
                        </select>
                    </div>
                </div>


                {/* -----------------------------------------------
            ACCOUNT LIST
            ----------------------------------------------- */}

                <div className="admin-account-list">
                    {loading && (
                        <div className="admin-empty-state">
                            Loading account directory…
                        </div>
                    )}

                    {!loading &&
                        visibleUsers.length === 0 && (
                            <div className="admin-empty-state">
                                No accounts match the current filters.
                            </div>
                        )}

                    {!loading &&
                        visibleUsers.map(
                            (
                                directoryUser,
                            ) => {
                                const expanded =
                                    expandedUserId
                                    === directoryUser.id;

                                const initials =
                                    `${directoryUser.first_name?.[0] ?? ''}${directoryUser.last_name?.[0] ?? ''}`;

                                return (
                                    <article
                                        key={
                                            directoryUser.id
                                        }
                                        className={
                                            expanded
                                                ? 'admin-account-row expanded'
                                                : 'admin-account-row'
                                        }
                                    >
                                        <button
                                            type="button"
                                            className="admin-account-summary"
                                            onClick={
                                                () =>
                                                    setExpandedUserId(
                                                        expanded
                                                            ? null
                                                            : directoryUser.id,
                                                    )
                                            }
                                        >
                                            <div className="admin-user-avatar">
                                                {initials || '?'}
                                            </div>

                                            <div className="admin-user-name">
                                                <strong>
                                                    {directoryUser.first_name}{' '}
                                                    {directoryUser.last_name}
                                                </strong>

                                                <span>
                                                    {directoryUser.email}
                                                </span>
                                            </div>

                                            <span
                                                className="admin-role-badge"
                                                data-role={
                                                    directoryUser.role
                                                }
                                            >
                                                {
                                                    roleLabel(
                                                        directoryUser.role,
                                                    )
                                                }
                                            </span>

                                            <span
                                                className="admin-status-badge"
                                                data-status={
                                                    directoryUser.account_status
                                                }
                                            >
                                                {
                                                    accountStatusLabel(
                                                        directoryUser.account_status,
                                                    )
                                                }
                                            </span>

                                            <div className="admin-row-expand">
                                                {
                                                    expanded
                                                        ? <ChevronDown size={18} />
                                                        : <ChevronRight size={18} />
                                                }
                                            </div>
                                        </button>


                                        {expanded && (
                                            <div className="admin-account-details">
                                                <div className="admin-detail-grid">
                                                    <div>
                                                        <span>
                                                            Email
                                                        </span>

                                                        <strong>
                                                            <Mail size={14} />

                                                            {directoryUser.email}
                                                        </strong>
                                                    </div>

                                                    <div>
                                                        <span>
                                                            Role
                                                        </span>

                                                        <strong>
                                                            {
                                                                roleLabel(
                                                                    directoryUser.role,
                                                                )
                                                            }
                                                        </strong>
                                                    </div>

                                                    <div>
                                                        <span>
                                                            Account status
                                                        </span>

                                                        <strong>
                                                            {
                                                                accountStatusLabel(
                                                                    directoryUser.account_status,
                                                                )
                                                            }
                                                        </strong>
                                                    </div>

                                                    <div>
                                                        <span>
                                                            MFA
                                                        </span>

                                                        <strong>
                                                            {
                                                                directoryUser.mfa_enabled
                                                                    ? 'Enabled'
                                                                    : 'Not enabled'
                                                            }
                                                        </strong>
                                                    </div>

                                                    <div>
                                                        <span>
                                                            Phone
                                                        </span>

                                                        <strong>
                                                            {
                                                                directoryUser.phone
                                                                || 'Not recorded'
                                                            }
                                                        </strong>
                                                    </div>

                                                    <div>
                                                        <span>
                                                            Date of birth
                                                        </span>

                                                        <strong>
                                                            {
                                                                directoryUser.date_of_birth
                                                                || 'Not recorded'
                                                            }
                                                        </strong>
                                                    </div>

                                                    <div>
                                                        <span>
                                                            Gender
                                                        </span>

                                                        <strong>
                                                            {
                                                                directoryUser.gender
                                                                || 'Not recorded'
                                                            }
                                                        </strong>
                                                    </div>

                                                    <div>
                                                        <span>
                                                            User ID
                                                        </span>

                                                        <strong className="admin-id-value">
                                                            {directoryUser.id}
                                                        </strong>
                                                    </div>
                                                </div>


                                                <div className="admin-account-actions">
                                                    <button
                                                        type="button"
                                                        className="button secondary"
                                                        onClick={
                                                            () =>
                                                                openEditDrawer(
                                                                    directoryUser,
                                                                )
                                                        }
                                                    >
                                                        <UserCog size={16} />

                                                        Edit account
                                                    </button>


                                                    {directoryUser.role
                                                        === 'CLINICIAN' && (
                                                            <button
                                                                type="button"
                                                                className="button secondary"
                                                                onClick={
                                                                    () =>
                                                                        openClinicianAssignments(
                                                                            directoryUser,
                                                                        )
                                                                }
                                                            >
                                                                <Stethoscope size={16} />

                                                                Manage patients
                                                            </button>
                                                        )}


                                                    {directoryUser.role
                                                        === 'USER' && (
                                                            <button
                                                                type="button"
                                                                className="button secondary"
                                                                onClick={
                                                                    () =>
                                                                        openUserRelationships(
                                                                            directoryUser,
                                                                        )
                                                                }
                                                            >
                                                                <UserCheck size={16} />

                                                                Manage relationships
                                                            </button>
                                                        )}


                                                    <button
                                                        type="button"
                                                        className="admin-more-button"
                                                        title="Role, status and account actions"
                                                        onClick={
                                                            () =>
                                                                openGovernanceDrawer(
                                                                    directoryUser,
                                                                )
                                                        }
                                                    >
                                                        <MoreHorizontal size={18} />
                                                    </button>
                                                </div>
                                            </div>
                                        )}
                                    </article>
                                );
                            },
                        )}
                </div>
            </section>


            {/* =================================================
                CLINICAL ASSIGNMENT MANAGEMENT

                This system-wide workspace complements the
                per-clinician and per-user relationship drawers.

                Administrators can:
                - inspect all active clinician-patient relationships;
                - filter assignments by clinician;
                - assign multiple patients at once;
                - remove existing assignments.

                Patient clinical records are not exposed here.
                ================================================= */}

            <section className="admin-assignment-workspace">

                {/* -------------------------------------------------
                SECTION HEADER
                ------------------------------------------------- */}

                <header className="admin-assignment-header">
                    <div>
                        <span className="eyebrow">
                            Clinical workforce
                        </span>

                        <h2>
                            Clinical assignment management
                        </h2>

                        <p>
                            Assign synthetic patients to clinicians and review
                            active care relationships across MEDISCOPE.
                        </p>
                    </div>

                    <div className="admin-assignment-header-icon">
                        <Stethoscope size={22} />
                    </div>
                </header>


                {/* =================================================
                ASSIGNMENT KPIs
                ================================================= */}

                <div className="assignment-summary-grid">
                    <div>
                        <span>
                            Active assignments
                        </span>

                        <strong>
                            {assignments.length}
                        </strong>

                        <small>
                            Current relationships
                        </small>
                    </div>

                    <div>
                        <span>
                            Assigned clinicians
                        </span>

                        <strong>
                            {assignedClinicianCount}
                        </strong>

                        <small>
                            Clinicians with patients
                        </small>
                    </div>

                    <div>
                        <span>
                            Assigned patients
                        </span>

                        <strong>
                            {assignedPatientCount}
                        </strong>

                        <small>
                            Patients with ≥1 clinician
                        </small>
                    </div>

                    <div>
                        <span>
                            Unassigned patients
                        </span>

                        <strong>
                            {unassignedPatientCount}
                        </strong>

                        <small>
                            No active clinician
                        </small>
                    </div>
                </div>


                {/* =================================================
                CREATE ASSIGNMENTS
                ================================================= */}

                <div className="assignment-builder">

                    {/* -----------------------------------------------
                    STEP 1 — SELECT CLINICIAN
                    ----------------------------------------------- */}

                    <section className="assignment-builder-clinician">
                        <div className="assignment-step-heading">
                            <span>
                                1
                            </span>

                            <div>
                                <strong>
                                    Select clinician
                                </strong>

                                <small>
                                    Choose the clinician who will receive the
                                    selected patients.
                                </small>
                            </div>
                        </div>

                        <label>
                            Clinician

                            <select
                                value={
                                    assignmentClinicianId
                                }
                                onChange={
                                    (
                                        event,
                                    ) => {
                                        setAssignmentClinicianId(
                                            event.target.value,
                                        );

                                        // Patient selection belongs to the
                                        // previously selected clinician and must
                                        // not carry over to a different account.
                                        setSelectedAssignmentPatientIds(
                                            [],
                                        );
                                    }
                                }
                            >
                                <option value="">
                                    Select clinician
                                </option>

                                {
                                    clinicians
                                        .filter(
                                            (
                                                clinician,
                                            ) =>
                                                clinician.account_status
                                                === 'ACTIVE',
                                        )
                                        .map(
                                            (
                                                clinician,
                                            ) => (
                                                <option
                                                    key={
                                                        clinician.id
                                                    }
                                                    value={
                                                        clinician.id
                                                    }
                                                >
                                                    {
                                                        clinician.first_name
                                                    }{' '}
                                                    {
                                                        clinician.last_name
                                                    }
                                                    {' · '}
                                                    {
                                                        clinician.email
                                                    }
                                                </option>
                                            ),
                                        )
                                }
                            </select>
                        </label>


                        {assignmentClinicianId && (
                            <div className="selected-clinician-summary">
                                <Stethoscope size={18} />

                                <div>
                                    <span>
                                        Selected clinician
                                    </span>

                                    <strong>
                                        {
                                            (() => {
                                                const clinician =
                                                    clinicians.find(
                                                        (
                                                            item,
                                                        ) =>
                                                            item.id
                                                            === assignmentClinicianId,
                                                    );

                                                return clinician
                                                    ? `${clinician.first_name} ${clinician.last_name}`
                                                    : 'Clinician';
                                            })()
                                        }
                                    </strong>
                                </div>

                                <b>
                                    {
                                        assignmentsForClinician(
                                            assignmentClinicianId,
                                        ).length
                                    } patient{
                                        assignmentsForClinician(
                                            assignmentClinicianId,
                                        ).length === 1
                                            ? ''
                                            : 's'
                                    }
                                </b>
                            </div>
                        )}
                    </section>


                    {/* -----------------------------------------------
                    STEP 2 — SELECT PATIENTS
                    ----------------------------------------------- */}

                    <section className="assignment-builder-patients">
                        <div className="assignment-step-heading">
                            <span>
                                2
                            </span>

                            <div>
                                <strong>
                                    Select patients
                                </strong>

                                <small>
                                    Multiple patients can be assigned in one
                                    administrative action.
                                </small>
                            </div>
                        </div>


                        {!assignmentClinicianId ? (
                            <div className="assignment-placeholder">
                                <Stethoscope size={22} />

                                <strong>
                                    Select a clinician first
                                </strong>

                                <span>
                                    Available synthetic patients will then appear
                                    here.
                                </span>
                            </div>
                        ) : (
                            <>
                                <div className="assignment-patient-search">
                                    <Search size={16} />

                                    <input
                                        type="search"
                                        placeholder="Search patient number, name, state or LGA"
                                        value={
                                            assignmentPatientSearch
                                        }
                                        onChange={
                                            (
                                                event,
                                            ) =>
                                                setAssignmentPatientSearch(
                                                    event.target.value,
                                                )
                                        }
                                    />
                                </div>


                                <div className="assignment-patient-list">
                                    {
                                        availableAssignmentPatients.length
                                            === 0
                                            ? (
                                                <div className="soft-empty">
                                                    No additional patients match the current
                                                    selection.
                                                </div>
                                            )
                                            : (
                                                availableAssignmentPatients.map(
                                                    (
                                                        patient,
                                                    ) => {
                                                        const checked =
                                                            selectedAssignmentPatientIds.includes(
                                                                patient.id,
                                                            );

                                                        return (
                                                            <label
                                                                key={
                                                                    patient.id
                                                                }
                                                                className={
                                                                    checked
                                                                        ? 'assignment-patient-option selected'
                                                                        : 'assignment-patient-option'
                                                                }
                                                            >
                                                                <input
                                                                    type="checkbox"
                                                                    checked={
                                                                        checked
                                                                    }
                                                                    onChange={
                                                                        () =>
                                                                            toggleAssignmentPatient(
                                                                                patient.id,
                                                                            )
                                                                    }
                                                                />

                                                                <div>
                                                                    <strong>
                                                                        {
                                                                            patient.synthetic_patient_number
                                                                        }
                                                                    </strong>

                                                                    <span>
                                                                        {
                                                                            [
                                                                                patient.first_name,
                                                                                patient.last_name,
                                                                            ]
                                                                                .filter(Boolean)
                                                                                .join(' ')
                                                                            || 'Synthetic patient'
                                                                        }
                                                                    </span>
                                                                </div>

                                                                <small>
                                                                    {
                                                                        [
                                                                            patient.state,
                                                                            patient.lga,
                                                                        ]
                                                                            .filter(Boolean)
                                                                            .join(' · ')
                                                                    }
                                                                </small>
                                                            </label>
                                                        );
                                                    },
                                                )
                                            )
                                    }
                                </div>


                                <div className="assignment-selection-footer">
                                    <span>
                                        {
                                            selectedAssignmentPatientIds.length
                                        } patient{
                                            selectedAssignmentPatientIds.length === 1
                                                ? ''
                                                : 's'
                                        } selected
                                    </span>

                                    <button
                                        type="button"
                                        className="button primary"
                                        disabled={
                                            assignmentBusy
                                            ||
                                            selectedAssignmentPatientIds.length
                                            === 0
                                        }
                                        onClick={
                                            assignSelectedPatients
                                        }
                                    >
                                        <UserCheck size={16} />

                                        {
                                            assignmentBusy
                                                ? 'Assigning…'
                                                : `Assign ${selectedAssignmentPatientIds.length
                                                || ''
                                                } patient${selectedAssignmentPatientIds.length === 1
                                                    ? ''
                                                    : 's'
                                                }`
                                        }
                                    </button>
                                </div>
                            </>
                        )}
                    </section>
                </div>


                {/* =================================================
                CURRENT ASSIGNMENT RELATIONSHIPS
                ================================================= */}

                <section className="assignment-directory">
                    <header className="assignment-directory-header">
                        <div>
                            <span className="eyebrow">
                                Active relationships
                            </span>

                            <h3>
                                Clinician-patient assignments
                            </h3>

                            <p>
                                Review and end active assignments without opening
                                an individual account.
                            </p>
                        </div>

                        <div className="assignment-directory-filter">
                            <Filter size={15} />

                            <select
                                value={
                                    assignmentClinicianFilter
                                }
                                onChange={
                                    (
                                        event,
                                    ) =>
                                        setAssignmentClinicianFilter(
                                            event.target.value,
                                        )
                                }
                            >
                                <option value="ALL">
                                    All clinicians
                                </option>

                                {
                                    clinicians.map(
                                        (
                                            clinician,
                                        ) => (
                                            <option
                                                key={
                                                    clinician.id
                                                }
                                                value={
                                                    clinician.id
                                                }
                                            >
                                                {
                                                    clinician.first_name
                                                }{' '}
                                                {
                                                    clinician.last_name
                                                }
                                            </option>
                                        ),
                                    )
                                }
                            </select>
                        </div>
                    </header>


                    <div className="assignment-table">

                        {/* -----------------------------------------------
                    TABLE HEADER
                    ----------------------------------------------- */}

                        <div className="assignment-table-row header">
                            <span>
                                Clinician
                            </span>

                            <span>
                                Patient
                            </span>

                            <span>
                                Assigned
                            </span>

                            <span>
                                Status
                            </span>

                            <span>
                                Action
                            </span>
                        </div>


                        {/* -----------------------------------------------
                    TABLE CONTENT
                    ----------------------------------------------- */}

                        {
                            globalAssignmentRows.length
                                === 0
                                ? (
                                    <div className="assignment-empty">
                                        No active clinician-patient assignments match
                                        this filter.
                                    </div>
                                )
                                : (
                                    globalAssignmentRows.map(
                                        (
                                            row,
                                        ) => (
                                            <div
                                                className="assignment-table-row"
                                                key={
                                                    row.assignment.id
                                                }
                                            >
                                                <div className="assignment-person">
                                                    <div className="assignment-avatar clinician">
                                                        {
                                                            row.clinician
                                                                ? `${row.clinician.first_name?.[0]
                                                                ?? ''
                                                                }${row.clinician.last_name?.[0]
                                                                ?? ''
                                                                }`
                                                                : '?'
                                                        }
                                                    </div>

                                                    <div>
                                                        <strong>
                                                            {
                                                                row.clinician
                                                                    ? `${row.clinician.first_name} ${row.clinician.last_name}`
                                                                    : 'Unknown clinician'
                                                            }
                                                        </strong>

                                                        <span>
                                                            {
                                                                row.clinician?.email
                                                                ?? row.assignment.clinician_user_id
                                                            }
                                                        </span>
                                                    </div>
                                                </div>


                                                <div className="assignment-person">
                                                    <div className="assignment-avatar patient">
                                                        <CircleUserRound size={16} />
                                                    </div>

                                                    <div>
                                                        <strong>
                                                            {
                                                                row.patient?.synthetic_patient_number
                                                                ?? row.assignment.patient_id
                                                            }
                                                        </strong>

                                                        <span>
                                                            {
                                                                row.patient
                                                                    ? [
                                                                        row.patient.first_name,
                                                                        row.patient.last_name,
                                                                    ]
                                                                        .filter(Boolean)
                                                                        .join(' ')
                                                                    || 'Synthetic patient'
                                                                    : 'Patient'
                                                            }
                                                        </span>
                                                    </div>
                                                </div>


                                                <span className="assignment-date">
                                                    {
                                                        new Date(
                                                            row.assignment.assigned_at,
                                                        ).toLocaleDateString(
                                                            [],
                                                            {
                                                                day: 'numeric',
                                                                month: 'short',
                                                                year: 'numeric',
                                                            },
                                                        )
                                                    }
                                                </span>


                                                <span className="assignment-status active">
                                                    Active
                                                </span>


                                                <button
                                                    type="button"
                                                    className="button secondary small"
                                                    disabled={
                                                        assignmentBusy
                                                    }
                                                    onClick={
                                                        () =>
                                                            endClinicianAssignment(
                                                                row.assignment.id,
                                                            )
                                                    }
                                                >
                                                    Unassign
                                                </button>
                                            </div>
                                        ),
                                    )
                                )
                        }
                    </div>
                </section>
            </section>


            {/* =================================================
          DRAWER BACKDROP
          ================================================= */}

            {drawerMode && (
                <div
                    className="admin-drawer-backdrop"
                    onMouseDown={
                        (
                            event,
                        ) => {
                            if (
                                event.target
                                === event.currentTarget
                            ) {
                                closeDrawer();
                            }
                        }
                    }
                >
                    <aside className="admin-drawer">

                        {/* -------------------------------------------
                DRAWER HEADER
                ------------------------------------------- */}

                        <header className="admin-drawer-header">
                            <div>
                                <span className="eyebrow">
                                    Administration
                                </span>

                                <h2>
                                    {
                                        drawerMode === 'CREATE'
                                            ? 'Create account'
                                            : drawerMode === 'EDIT'
                                                ? 'Edit account'
                                                : drawerMode === 'GOVERNANCE'
                                                    ? 'Account governance'
                                                    : drawerMode === 'CLINICIAN_ASSIGNMENTS'
                                                        ? 'Patient assignments'
                                                        : 'User relationships'
                                    }
                                </h2>

                                {selectedUser && (
                                    <p>
                                        {selectedUser.first_name}{' '}
                                        {selectedUser.last_name}
                                    </p>
                                )}
                            </div>

                            <button
                                type="button"
                                className="icon-button"
                                onClick={
                                    closeDrawer
                                }
                                aria-label="Close administration panel"
                            >
                                <X size={19} />
                            </button>
                        </header>


                        <div className="admin-drawer-content">
                            {error && (
                                <div className="form-error">
                                    {error}
                                </div>
                            )}

                            {message && (
                                <div className="form-info">
                                    {message}
                                </div>
                            )}


                            {/* =========================================
                  CREATE ACCOUNT
                  ========================================= */}

                            {drawerMode === 'CREATE' && (
                                <form
                                    className="admin-drawer-form"
                                    onSubmit={
                                        createAccount
                                    }
                                >
                                    <div className="two-col">
                                        <label>
                                            First name

                                            <input
                                                required
                                                value={
                                                    createForm.first_name
                                                }
                                                onChange={
                                                    (
                                                        event,
                                                    ) =>
                                                        setCreateForm({
                                                            ...createForm,
                                                            first_name:
                                                                event.target.value,
                                                        })
                                                }
                                            />
                                        </label>

                                        <label>
                                            Last name

                                            <input
                                                required
                                                value={
                                                    createForm.last_name
                                                }
                                                onChange={
                                                    (
                                                        event,
                                                    ) =>
                                                        setCreateForm({
                                                            ...createForm,
                                                            last_name:
                                                                event.target.value,
                                                        })
                                                }
                                            />
                                        </label>
                                    </div>

                                    <label>
                                        Email

                                        <input
                                            type="email"
                                            required
                                            value={
                                                createForm.email
                                            }
                                            onChange={
                                                (
                                                    event,
                                                ) =>
                                                    setCreateForm({
                                                        ...createForm,
                                                        email:
                                                            event.target.value,
                                                    })
                                            }
                                        />
                                    </label>

                                    <label>
                                        Temporary password

                                        <PasswordInput
                                            required
                                            minLength={12}
                                            maxLength={200}
                                            autoComplete="new-password"
                                            value={
                                                createForm.password
                                            }
                                            onChange={
                                                (
                                                    event,
                                                ) =>
                                                    setCreateForm({
                                                        ...createForm,
                                                        password:
                                                            event.target.value,
                                                    })
                                            }
                                        />
                                    </label>

                                    <div className="two-col">
                                        <label>
                                            Date of birth

                                            <input
                                                type="date"
                                                max={
                                                    new Date()
                                                        .toISOString()
                                                        .slice(
                                                            0,
                                                            10,
                                                        )
                                                }
                                                value={
                                                    createForm.date_of_birth
                                                }
                                                onChange={
                                                    (
                                                        event,
                                                    ) =>
                                                        setCreateForm({
                                                            ...createForm,
                                                            date_of_birth:
                                                                event.target.value,
                                                        })
                                                }
                                            />
                                        </label>

                                        <label>
                                            Gender

                                            <select
                                                value={
                                                    createForm.gender
                                                }
                                                onChange={
                                                    (
                                                        event,
                                                    ) =>
                                                        setCreateForm({
                                                            ...createForm,
                                                            gender:
                                                                event.target.value,
                                                        })
                                                }
                                            >
                                                <option value="">
                                                    Not specified
                                                </option>

                                                <option value="Male">
                                                    Male
                                                </option>

                                                <option value="Female">
                                                    Female
                                                </option>
                                            </select>
                                        </label>
                                    </div>

                                    <label>
                                        Phone

                                        <input
                                            type="tel"
                                            value={
                                                createForm.phone
                                            }
                                            onChange={
                                                (
                                                    event,
                                                ) =>
                                                    setCreateForm({
                                                        ...createForm,
                                                        phone:
                                                            event.target.value,
                                                    })
                                            }
                                        />
                                    </label>

                                    <label>
                                        Role

                                        <select
                                            value={
                                                createForm.role
                                            }
                                            onChange={
                                                (
                                                    event,
                                                ) =>
                                                    setCreateForm({
                                                        ...createForm,
                                                        role:
                                                            event.target.value as Role,
                                                    })
                                            }
                                        >
                                            {
                                                (
                                                    metadata?.roles
                                                    ?? [
                                                        'USER',
                                                        'CLINICIAN',
                                                        'ADMINISTRATOR',
                                                    ]
                                                ).map(
                                                    (
                                                        role,
                                                    ) => (
                                                        <option
                                                            key={
                                                                role
                                                            }
                                                            value={
                                                                role
                                                            }
                                                        >
                                                            {
                                                                roleLabel(
                                                                    role,
                                                                )
                                                            }
                                                        </option>
                                                    ),
                                                )
                                            }
                                        </select>
                                    </label>

                                    <div className="admin-drawer-note">
                                        Administrator-created accounts are
                                        activated and email-verified by the
                                        backend. Privileged users will still be
                                        required to enrol MFA at sign-in.
                                    </div>

                                    <div className="admin-drawer-actions">
                                        <button
                                            type="button"
                                            className="button secondary"
                                            onClick={
                                                closeDrawer
                                            }
                                        >
                                            Cancel
                                        </button>

                                        <button
                                            className="button primary"
                                            disabled={
                                                actionBusy
                                            }
                                        >
                                            <UserPlus size={17} />

                                            {
                                                actionBusy
                                                    ? 'Creating…'
                                                    : 'Create account'
                                            }
                                        </button>
                                    </div>
                                </form>
                            )}


                            {/* =========================================
                  EDIT ACCOUNT
                  ========================================= */}

                            {drawerMode === 'EDIT'
                                && selectedUser && (
                                    <form
                                        className="admin-drawer-form"
                                        onSubmit={
                                            updateAccount
                                        }
                                    >
                                        <div className="two-col">
                                            <label>
                                                First name

                                                <input
                                                    required
                                                    value={
                                                        editForm.first_name
                                                    }
                                                    onChange={
                                                        (
                                                            event,
                                                        ) =>
                                                            setEditForm({
                                                                ...editForm,
                                                                first_name:
                                                                    event.target.value,
                                                            })
                                                    }
                                                />
                                            </label>

                                            <label>
                                                Last name

                                                <input
                                                    required
                                                    value={
                                                        editForm.last_name
                                                    }
                                                    onChange={
                                                        (
                                                            event,
                                                        ) =>
                                                            setEditForm({
                                                                ...editForm,
                                                                last_name:
                                                                    event.target.value,
                                                            })
                                                    }
                                                />
                                            </label>
                                        </div>

                                        <label>
                                            Email

                                            <input
                                                value={
                                                    selectedUser.email
                                                }
                                                disabled
                                            />

                                            <span className="field-help">
                                                Email changes require a separate
                                                verification workflow.
                                            </span>
                                        </label>

                                        <div className="two-col">
                                            <label>
                                                Date of birth

                                                <input
                                                    type="date"
                                                    value={
                                                        editForm.date_of_birth
                                                    }
                                                    onChange={
                                                        (
                                                            event,
                                                        ) =>
                                                            setEditForm({
                                                                ...editForm,
                                                                date_of_birth:
                                                                    event.target.value,
                                                            })
                                                    }
                                                />
                                            </label>

                                            <label>
                                                Gender

                                                <select
                                                    value={
                                                        editForm.gender
                                                    }
                                                    onChange={
                                                        (
                                                            event,
                                                        ) =>
                                                            setEditForm({
                                                                ...editForm,
                                                                gender:
                                                                    event.target.value,
                                                            })
                                                    }
                                                >
                                                    <option value="">
                                                        Not specified
                                                    </option>

                                                    <option value="Male">
                                                        Male
                                                    </option>

                                                    <option value="Female">
                                                        Female
                                                    </option>
                                                </select>
                                            </label>
                                        </div>

                                        <label>
                                            Phone

                                            <input
                                                type="tel"
                                                value={
                                                    editForm.phone
                                                }
                                                onChange={
                                                    (
                                                        event,
                                                    ) =>
                                                        setEditForm({
                                                            ...editForm,
                                                            phone:
                                                                event.target.value,
                                                        })
                                                }
                                            />
                                        </label>

                                        <div className="admin-drawer-actions">
                                            <button
                                                type="button"
                                                className="button secondary"
                                                onClick={
                                                    closeDrawer
                                                }
                                            >
                                                Cancel
                                            </button>

                                            <button
                                                className="button primary"
                                                disabled={
                                                    actionBusy
                                                }
                                            >
                                                {
                                                    actionBusy
                                                        ? 'Saving…'
                                                        : 'Save changes'
                                                }
                                            </button>
                                        </div>
                                    </form>
                                )}


                            {/* =========================================
                  ACCOUNT GOVERNANCE
                  ========================================= */}

                            {drawerMode === 'GOVERNANCE'
                                && selectedUser && (
                                    <div className="admin-governance-drawer">
                                        <section>
                                            <span className="eyebrow">
                                                Access level
                                            </span>

                                            <h3>
                                                Application role
                                            </h3>

                                            <p>
                                                Changing a role can affect access and
                                                existing patient relationships.
                                            </p>

                                            <select
                                                value={
                                                    governanceRole
                                                }
                                                onChange={
                                                    (
                                                        event,
                                                    ) =>
                                                        setGovernanceRole(event.target.value as Role,
                                                        )
                                                }
                                            >
                                                {
                                                    (
                                                        metadata?.roles
                                                        ?? []
                                                    ).map(
                                                        (
                                                            role,
                                                        ) => (
                                                            <option
                                                                key={
                                                                    role
                                                                }
                                                                value={
                                                                    role
                                                                }
                                                            >
                                                                {
                                                                    roleLabel(
                                                                        role,
                                                                    )
                                                                }
                                                            </option>
                                                        ),
                                                    )
                                                }
                                            </select>
                                        </section>


                                        <section>
                                            <span className="eyebrow">
                                                Account lifecycle
                                            </span>

                                            <h3>
                                                Account status
                                            </h3>

                                            <p>
                                                Only statuses supported by the backend
                                                policy are shown.
                                            </p>

                                            <select
                                                value={
                                                    governanceStatus
                                                }
                                                onChange={
                                                    (
                                                        event,
                                                    ) =>
                                                        setGovernanceStatus(
                                                            event.target.value,
                                                        )
                                                }
                                            >
                                                {
                                                    (
                                                        metadata?.account_statuses
                                                        ?? [
                                                            selectedUser.account_status,
                                                        ]
                                                    ).map(
                                                        (
                                                            status,
                                                        ) => (
                                                            <option
                                                                key={
                                                                    status
                                                                }
                                                                value={
                                                                    status
                                                                }
                                                            >
                                                                {
                                                                    accountStatusLabel(
                                                                        status,
                                                                    )
                                                                }
                                                            </option>
                                                        ),
                                                    )
                                                }
                                            </select>
                                        </section>


                                        {
                                            selectedUser.id
                                            === currentAdmin?.id && (
                                                <div className="admin-warning-note">
                                                    Your own administrator account is
                                                    protected from self-demotion,
                                                    self-disabling and deletion by the
                                                    backend.
                                                </div>
                                            )
                                        }


                                        <div className="admin-drawer-actions">
                                            <button
                                                type="button"
                                                className="button secondary"
                                                onClick={
                                                    closeDrawer
                                                }
                                            >
                                                Cancel
                                            </button>

                                            <button
                                                type="button"
                                                className="button primary"
                                                disabled={
                                                    actionBusy
                                                }
                                                onClick={
                                                    saveGovernance
                                                }
                                            >
                                                Save governance
                                            </button>
                                        </div>


                                        <section className="admin-danger-zone">
                                            <span className="eyebrow">
                                                Danger zone
                                            </span>

                                            <h3>
                                                Remove account
                                            </h3>

                                            <p>
                                                MEDISCOPE uses soft deletion so
                                                historical audit information is
                                                preserved.
                                            </p>

                                            <button
                                                type="button"
                                                className="button danger-button"
                                                disabled={
                                                    actionBusy
                                                    ||
                                                    selectedUser.id
                                                    === currentAdmin?.id
                                                }
                                                onClick={
                                                    deleteAccount
                                                }
                                            >
                                                <Trash2 size={16} />

                                                Soft-delete account
                                            </button>
                                        </section>
                                    </div>
                                )}


                            {/* =========================================
                  CLINICIAN ASSIGNMENTS
                  ========================================= */}

                            {drawerMode === 'CLINICIAN_ASSIGNMENTS'
                                && selectedUser && (
                                    <div className="admin-relationship-drawer">
                                        <section>
                                            <span className="eyebrow">
                                                Clinical workload
                                            </span>

                                            <h3>
                                                Assigned patients
                                            </h3>

                                            {
                                                selectedClinicianAssignments.length
                                                    === 0
                                                    ? (
                                                        <div className="soft-empty">
                                                            No active patient assignments.
                                                        </div>
                                                    )
                                                    : (
                                                        <div className="admin-assignment-list">
                                                            {
                                                                selectedClinicianAssignments.map(
                                                                    (
                                                                        assignment,
                                                                    ) => {
                                                                        const patient =
                                                                            patientById(
                                                                                assignment.patient_id,
                                                                            );

                                                                        return (
                                                                            <div
                                                                                key={
                                                                                    assignment.id
                                                                                }
                                                                                className="admin-assignment-row"
                                                                            >
                                                                                <div>
                                                                                    <strong>
                                                                                        {
                                                                                            patient
                                                                                                ? patientLabel(
                                                                                                    patient,
                                                                                                )
                                                                                                : assignment.patient_id
                                                                                        }
                                                                                    </strong>

                                                                                    <span>
                                                                                        Assigned{' '}
                                                                                        {
                                                                                            new Date(
                                                                                                assignment.assigned_at,
                                                                                            )
                                                                                                .toLocaleDateString()
                                                                                        }
                                                                                    </span>
                                                                                </div>

                                                                                <button
                                                                                    type="button"
                                                                                    className="button secondary small"
                                                                                    disabled={
                                                                                        actionBusy
                                                                                    }
                                                                                    onClick={
                                                                                        () =>
                                                                                            endClinicianAssignment(
                                                                                                assignment.id,
                                                                                            )
                                                                                    }
                                                                                >
                                                                                    Remove
                                                                                </button>
                                                                            </div>
                                                                        );
                                                                    },
                                                                )
                                                            }
                                                        </div>
                                                    )
                                            }
                                        </section>


                                        <section>
                                            <span className="eyebrow">
                                                New assignment
                                            </span>

                                            <h3>
                                                Assign another patient
                                            </h3>

                                            <select
                                                value={
                                                    patientSelection
                                                }
                                                onChange={
                                                    (
                                                        event,
                                                    ) =>
                                                        setPatientSelection(
                                                            event.target.value,
                                                        )
                                                }
                                            >
                                                <option value="">
                                                    Select patient
                                                </option>

                                                {
                                                    patients
                                                        .filter(
                                                            (
                                                                patient,
                                                            ) =>
                                                                !selectedClinicianAssignments.some(
                                                                    (
                                                                        assignment,
                                                                    ) =>
                                                                        assignment.patient_id
                                                                        === patient.id,
                                                                ),
                                                        )
                                                        .map(
                                                            (
                                                                patient,
                                                            ) => (
                                                                <option
                                                                    key={
                                                                        patient.id
                                                                    }
                                                                    value={
                                                                        patient.id
                                                                    }
                                                                >
                                                                    {
                                                                        patientLabel(
                                                                            patient,
                                                                        )
                                                                    }
                                                                </option>
                                                            ),
                                                        )
                                                }
                                            </select>

                                            <button
                                                type="button"
                                                className="button primary wide"
                                                disabled={
                                                    !patientSelection
                                                    ||
                                                    actionBusy
                                                }
                                                onClick={
                                                    assignSelectedPatient
                                                }
                                            >
                                                <Stethoscope size={16} />

                                                Assign patient
                                            </button>
                                        </section>
                                    </div>
                                )}


                            {/* =========================================
                  STANDARD USER RELATIONSHIPS
                  ========================================= */}

                            {drawerMode === 'USER_RELATIONSHIPS'
                                && selectedUser && (
                                    <div className="admin-relationship-drawer">

                                        {/* -------------------------------------
                      USER ↔ PATIENT
                      ------------------------------------- */}

                                        <section>
                                            <span className="eyebrow">
                                                Patient identity
                                            </span>

                                            <h3>
                                                Linked synthetic profile
                                            </h3>

                                            {
                                                selectedLinkedPatient
                                                    ? (
                                                        <div className="admin-linked-patient">
                                                            <div>
                                                                <strong>
                                                                    {
                                                                        patientLabel(
                                                                            selectedLinkedPatient,
                                                                        )
                                                                    }
                                                                </strong>

                                                                <span>
                                                                    {
                                                                        [
                                                                            selectedLinkedPatient.state,
                                                                            selectedLinkedPatient.lga,
                                                                        ]
                                                                            .filter(Boolean)
                                                                            .join(' · ')
                                                                    }
                                                                </span>
                                                            </div>

                                                            <button
                                                                type="button"
                                                                className="button secondary small"
                                                                disabled={
                                                                    actionBusy
                                                                }
                                                                onClick={
                                                                    () =>
                                                                        unlinkPatient(
                                                                            selectedLinkedPatient.id,
                                                                        )
                                                                }
                                                            >
                                                                <Unlink size={15} />

                                                                Unlink
                                                            </button>
                                                        </div>
                                                    )
                                                    : (
                                                        <>
                                                            <div className="soft-empty">
                                                                This account is not linked to a
                                                                synthetic patient profile.
                                                            </div>

                                                            <select
                                                                value={
                                                                    patientSelection
                                                                }
                                                                onChange={
                                                                    (
                                                                        event,
                                                                    ) =>
                                                                        setPatientSelection(
                                                                            event.target.value,
                                                                        )
                                                                }
                                                            >
                                                                <option value="">
                                                                    Select unlinked patient
                                                                </option>

                                                                {
                                                                    patients
                                                                        .filter(
                                                                            (
                                                                                patient,
                                                                            ) =>
                                                                                !patient.linked_user_id,
                                                                        )
                                                                        .map(
                                                                            (
                                                                                patient,
                                                                            ) => (
                                                                                <option
                                                                                    key={
                                                                                        patient.id
                                                                                    }
                                                                                    value={
                                                                                        patient.id
                                                                                    }
                                                                                >
                                                                                    {
                                                                                        patientLabel(
                                                                                            patient,
                                                                                        )
                                                                                    }
                                                                                </option>
                                                                            ),
                                                                        )
                                                                }
                                                            </select>

                                                            <button
                                                                type="button"
                                                                className="button primary wide"
                                                                disabled={
                                                                    !patientSelection
                                                                    ||
                                                                    actionBusy
                                                                }
                                                                onClick={
                                                                    linkSelectedPatient
                                                                }
                                                            >
                                                                <Link2 size={16} />

                                                                Link patient profile
                                                            </button>
                                                        </>
                                                    )
                                            }
                                        </section>


                                        {/* -------------------------------------
                      PATIENT ↔ CLINICIANS
                      ------------------------------------- */}

                                        {selectedLinkedPatient && (
                                            <section>
                                                <span className="eyebrow">
                                                    Care relationships
                                                </span>

                                                <h3>
                                                    Assigned clinicians
                                                </h3>

                                                {
                                                    selectedPatientAssignments.length
                                                        === 0
                                                        ? (
                                                            <div className="soft-empty">
                                                                No clinician is currently
                                                                assigned to this patient.
                                                            </div>
                                                        )
                                                        : (
                                                            <div className="admin-assignment-list">
                                                                {
                                                                    selectedPatientAssignments.map(
                                                                        (
                                                                            assignment,
                                                                        ) => {
                                                                            const clinician =
                                                                                clinicianById(
                                                                                    assignment.clinician_user_id,
                                                                                );

                                                                            return (
                                                                                <div
                                                                                    className="admin-assignment-row"
                                                                                    key={
                                                                                        assignment.id
                                                                                    }
                                                                                >
                                                                                    <div>
                                                                                        <strong>
                                                                                            {
                                                                                                clinician
                                                                                                    ? `${clinician.first_name} ${clinician.last_name}`
                                                                                                    : assignment.clinician_user_id
                                                                                            }
                                                                                        </strong>

                                                                                        <span>
                                                                                            {
                                                                                                clinician?.email
                                                                                                ?? 'Clinician'
                                                                                            }
                                                                                        </span>
                                                                                    </div>

                                                                                    <button
                                                                                        type="button"
                                                                                        className="button secondary small"
                                                                                        disabled={
                                                                                            actionBusy
                                                                                        }
                                                                                        onClick={
                                                                                            () =>
                                                                                                endClinicianAssignment(
                                                                                                    assignment.id,
                                                                                                )
                                                                                        }
                                                                                    >
                                                                                        Remove
                                                                                    </button>
                                                                                </div>
                                                                            );
                                                                        },
                                                                    )
                                                                }
                                                            </div>
                                                        )
                                                }


                                                <select
                                                    value={
                                                        patientSelection
                                                    }
                                                    onChange={
                                                        (
                                                            event,
                                                        ) =>
                                                            setPatientSelection(
                                                                event.target.value,
                                                            )
                                                    }
                                                >
                                                    <option value="">
                                                        Select clinician
                                                    </option>

                                                    {
                                                        clinicians
                                                            .filter(
                                                                (
                                                                    clinician,
                                                                ) =>
                                                                    clinician.account_status
                                                                    === 'ACTIVE'
                                                                    &&
                                                                    !selectedPatientAssignments.some(
                                                                        (
                                                                            assignment,
                                                                        ) =>
                                                                            assignment.clinician_user_id
                                                                            === clinician.id,
                                                                    ),
                                                            )
                                                            .map(
                                                                (
                                                                    clinician,
                                                                ) => (
                                                                    <option
                                                                        key={
                                                                            clinician.id
                                                                        }
                                                                        value={
                                                                            clinician.id
                                                                        }
                                                                    >
                                                                        {
                                                                            clinician.first_name
                                                                        }{' '}
                                                                        {
                                                                            clinician.last_name
                                                                        }
                                                                    </option>
                                                                ),
                                                            )
                                                    }
                                                </select>

                                                <button
                                                    type="button"
                                                    className="button primary wide"
                                                    disabled={
                                                        !patientSelection
                                                        ||
                                                        actionBusy
                                                    }
                                                    onClick={
                                                        async () => {
                                                            if (
                                                                !selectedLinkedPatient
                                                                ||
                                                                !patientSelection
                                                            ) {
                                                                return;
                                                            }

                                                            setActionBusy(
                                                                true,
                                                            );

                                                            setError('');

                                                            try {
                                                                await api.adminAssignClinician(
                                                                    patientSelection,
                                                                    selectedLinkedPatient.id,
                                                                );

                                                                await loadAdministration();

                                                                setPatientSelection(
                                                                    '',
                                                                );

                                                                setMessage(
                                                                    'Clinician assigned successfully.',
                                                                );
                                                            } catch (
                                                            errorValue
                                                            ) {
                                                                setError(
                                                                    errorValue instanceof Error
                                                                        ? errorValue.message
                                                                        : 'Unable to assign clinician.',
                                                                );
                                                            } finally {
                                                                setActionBusy(
                                                                    false,
                                                                );
                                                            }
                                                        }
                                                    }
                                                >
                                                    <UserCheck size={16} />

                                                    Assign clinician
                                                </button>
                                            </section>
                                        )}
                                    </div>
                                )}
                        </div>
                    </aside>
                </div>
            )}
        </>
    );
}
