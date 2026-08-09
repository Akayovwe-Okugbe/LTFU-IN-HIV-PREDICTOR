import { Route, Routes } from 'react-router-dom';
import { AppShell } from './components/AppShell';
import { ProtectedRoute } from './components/ProtectedRoute';
import AboutPage from './pages/AboutPage';
import AdministrationPage from './pages/AdministrationPage';
import { ForgotPasswordPage, LoginPage, RegisterPage, VerifyEmailPage } from './pages/AuthPages';
import ChangeRequestsPage from './pages/ChangeRequestsPage';
import ContactPage from './pages/ContactPage';
import DashboardPage from './pages/DashboardPage';
import LandingPage from './pages/LandingPage';
import MessagesPage from './pages/MessagesPage';
import NotFoundPage from './pages/NotFoundPage';
import PatientDetailPage from './pages/PatientDetailPage';
import PatientsPage from './pages/PatientsPage';
import PredictionsPage from './pages/PredictionsPage';
import SettingsPage from './pages/SettingsPage';

export default function App(){return <Routes><Route path="/" element={<LandingPage/>}/><Route path="/about" element={<AboutPage/>}/><Route path="/contact" element={<ContactPage/>}/><Route path="/login" element={<LoginPage/>}/><Route path="/register" element={<RegisterPage/>}/><Route path="/verify-email" element={<VerifyEmailPage/>}/><Route path="/forgot-password" element={<ForgotPasswordPage/>}/><Route path="/app" element={<ProtectedRoute><AppShell/></ProtectedRoute>}><Route index element={<DashboardPage/>}/><Route path="patients" element={<ProtectedRoute roles={['CLINICIAN']}><PatientsPage/></ProtectedRoute>}/><Route path="patients/:id" element={<ProtectedRoute roles={['CLINICIAN']}><PatientDetailPage/></ProtectedRoute>}/><Route path="predictions" element={<ProtectedRoute roles={['CLINICIAN']}><PredictionsPage/></ProtectedRoute>}/><Route path="messages" element={<MessagesPage/>}/><Route path="change-requests" element={<ProtectedRoute roles={['CLINICIAN']}><ChangeRequestsPage/></ProtectedRoute>}/><Route path="administration" element={<ProtectedRoute roles={['ADMINISTRATOR']}><AdministrationPage/></ProtectedRoute>}/><Route path="settings" element={<SettingsPage/>}/></Route><Route path="*" element={<NotFoundPage/>}/></Routes>}
