import type {
  ForwardRefExoticComponent,
  RefAttributes,
} from 'react';

import {
  Bell,
  BrainCircuit,
  ClipboardList,
  Gauge,
  HeartPulse,
  LogOut,
  MessageSquare,
  Settings,
  Stethoscope,
  UserRound,
  Users,
  ScrollText,
  type LucideProps,
} from 'lucide-react';

import {
  NavLink,
  Outlet,
  useNavigate,
} from 'react-router-dom';

import { Brand } from './Brand';
import { useAuth } from '../context/AuthContext';


// =====================================================
// NAVIGATION ITEM TYPE
// =====================================================

/**
 * Represents one sidebar navigation item.
 *
 * `end` is optional because only the dashboard route
 * needs exact path matching.
 */
type NavigationItem = {
  to: string;

  label: string;

  icon: ForwardRefExoticComponent<
    Omit<
      LucideProps,
      'ref'
    >
    & RefAttributes<SVGSVGElement>
  >;

  end?: boolean;
};


// =====================================================
// APPLICATION SHELL
// =====================================================

/**
 * Shared authenticated application layout.
 *
 * Responsibilities:
 * - render role-aware sidebar navigation;
 * - display authenticated user details;
 * - provide access to messages;
 * - provide logout behaviour;
 * - render the active child route via <Outlet />.
 *
 * Important:
 * Frontend role-aware navigation improves usability only.
 * Backend RBAC remains the authoritative security layer.
 */
export function AppShell() {
  const {
    user,
    logout,
  } = useAuth();

  const navigate =
    useNavigate();


  // ===================================================
  // NAVIGATION AVAILABLE TO ALL AUTHENTICATED USERS
  // ===================================================

  const commonNavigation:
    NavigationItem[] = [
      {
        to: '/app',

        label:
          user?.role === 'USER'
            ? 'My Health'
            : 'Overview',

        icon:
          user?.role === 'USER'
            ? HeartPulse
            : Gauge,

        // Prevent /app from remaining highlighted while
        // the user is on another nested route.
        end: true,
      },

      {
        to: '/app/messages',
        label: 'Messages',
        icon: MessageSquare,
      },

      {
        to: '/app/profile',
        label: 'Profile',
        icon: UserRound,
      },

      {
        to: '/app/settings',
        label: 'Security',
        icon: Settings,
      },
    ];


  // ===================================================
  // CLINICIAN-ONLY NAVIGATION
  // ===================================================

  const clinicianNavigation:
    NavigationItem[] = [
      {
        to: '/app/patients',
        label: 'Patients',
        icon: Stethoscope,
      },

      {
        to: '/app/predictions',
        label: 'Predictions',
        icon: BrainCircuit,
      },

      {
        to: '/app/change-requests',
        label: 'Change Requests',
        icon: ClipboardList,
      },
    ];


  // ===================================================
  // ADMINISTRATOR-ONLY NAVIGATION
  // ===================================================

  const administratorNavigation:
    NavigationItem[] = [
      {
        to: '/app/administration',
        label: 'Administration',
        icon: Users,
      },

      {
        to: '/app/audit-logs',
        label: 'Audit Logs',
        icon: ScrollText,
      },
    ];


  // ===================================================
  // ROLE-AWARE NAVIGATION ASSEMBLY
  // ===================================================

  const navigationLinks:
    NavigationItem[] =
    user?.role === 'ADMINISTRATOR'
      ? [
        ...commonNavigation,
        ...administratorNavigation,
      ]
      : user?.role === 'CLINICIAN'
        ? [
          ...commonNavigation,
          ...clinicianNavigation,
        ]
        : commonNavigation;


  // ===================================================
  // SIGN OUT
  // ===================================================

  function signOut() {
    logout();

    navigate(
      '/login',
      {
        replace: true,
      },
    );
  }


  // ===================================================
  // USER INITIALS
  // ===================================================

  const initials =
    `${user?.first_name?.[0] ?? ''}${user?.last_name?.[0] ?? ''}`;


  // ===================================================
  // RENDER
  // ===================================================

  return (
    <div className="app-shell">

      {/* =================================================
          SIDEBAR
          ================================================= */}

      <aside className="sidebar">
        <Brand />

        <nav
          className="sidebar-nav"
          aria-label="Primary navigation"
        >
          {
            navigationLinks.map(
              ({
                to,
                label,
                icon: Icon,
                end,
              }) => (
                <NavLink
                  key={to}
                  to={to}
                  end={end}
                  className={
                    ({
                      isActive,
                    }) =>
                      `nav-item ${isActive
                        ? 'active'
                        : ''
                      }`
                  }
                >
                  <Icon size={19} />

                  <span>
                    {label}
                  </span>
                </NavLink>
              ),
            )
          }
        </nav>


        {/* ===============================================
            CURRENT USER / LOGOUT
            =============================================== */}

        <div className="sidebar-footer">
          <div className="sidebar-user">
            <div
              className="avatar"
              aria-hidden="true"
            >
              {initials}
            </div>

            <div>
              <strong>
                {user?.first_name}{' '}
                {user?.last_name}
              </strong>

              <span>
                {user?.role}
              </span>
            </div>
          </div>

          <button
            type="button"
            className="icon-button"
            onClick={signOut}
            title="Sign out"
            aria-label="Sign out"
          >
            <LogOut size={18} />
          </button>
        </div>
      </aside>


      {/* =================================================
          MAIN APPLICATION AREA
          ================================================= */}

      <main className="app-main">

        {/* ===============================================
            TOP BAR
            =============================================== */}

        <header className="topbar">
          <span className="eyebrow">
            {
              user?.role === 'USER'
                ? 'Your MEDISCOPE account'
                : 'MEDISCOPE workspace'
            }
          </span>

          <div className="topbar-actions">

            {/* -------------------------------------------
                MESSAGE SHORTCUT
                ------------------------------------------- */}

            <button
              type="button"
              className="icon-button"
              onClick={
                () =>
                  navigate(
                    '/app/messages',
                  )
              }
              title="Open messages"
              aria-label="Open messages"
            >
              <Bell size={18} />
            </button>

            {/* -------------------------------------------
                SECURE SESSION STATUS
                ------------------------------------------- */}

            <span
              className="status-dot"
              aria-hidden="true"
            />

            <span>
              Secure session
            </span>
          </div>
        </header>


        {/* ===============================================
            ACTIVE CHILD PAGE
            =============================================== */}

        <div className="app-content">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
