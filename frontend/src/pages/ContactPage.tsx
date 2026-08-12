import {
    BookOpen,
    GraduationCap,
    Mail,
    MapPin,
    MessageCircle,
    ShieldCheck,
} from 'lucide-react';

import {
    Link,
} from 'react-router-dom';

import {
    Brand,
} from '../components/Brand';


// =====================================================
// CONTACT PAGE
// =====================================================

/**
 * Public project contact page.
 *
 * No live contact form is submitted from this prototype
 * yet. The page provides project context and clearly
 * identifies where deployment-specific contact details
 * should be added.
 */
export default function ContactPage() {
    return (
        <div className="simple-page">

            {/* =================================================
          NAVIGATION
          ================================================= */}

            <header className="marketing-nav">
                <Brand />

                <Link
                    className="button ghost small"
                    to="/"
                >
                    Back home
                </Link>
            </header>


            <main>

                {/* =================================================
            HERO
            ================================================= */}

                <section className="simple-hero contact-hero">
                    <span className="eyebrow">
                        Contact
                    </span>

                    <h1>
                        Questions about the MEDISCOPE prototype?
                    </h1>

                    <p className="simple-hero-lead">
                        MEDISCOPE is an academic healthcare
                        decision-support prototype exploring secure,
                        auditable LTFU risk estimation and
                        role-aware clinical workflows.
                    </p>
                </section>


                {/* =================================================
            CONTACT OPTIONS
            ================================================= */}

                <section className="contact-options">
                    <article className="contact-primary-card">
                        <div className="contact-icon">
                            <Mail size={23} />
                        </div>

                        <span className="eyebrow">
                            Project enquiries
                        </span>

                        <h2 className="section-heading-dark">
                            Email
                        </h2>

                        <p className="section-paragraph-dark">
                            Reach out to the project team for questions about
                            the MEDISCOPE prototype, its architecture,
                            machine learning or synthetic-data workflows.
                        </p>

                        <a
                            className="contact-email"
                            href="mailto:mediscope.ltfu@gmail.com"
                        >
                            mediscope.ltfu@gmail.com
                        </a>
                    </article>


                    <div className="contact-context-grid">
                        <article>
                            <GraduationCap size={21} />

                            <h3>
                                Academic context
                            </h3>

                            <p>
                                Developed as a Rome Business School
                                capstone project exploring machine learning,
                                healthcare workflow design and secure
                                application architecture.
                            </p>
                        </article>

                        <article>
                            <MapPin size={21} />

                            <h3>
                                Project setting
                            </h3>

                            <p>
                                MEDISCOPE models HIV retention-support
                                workflows using synthetic healthcare data
                                within a controlled demonstration
                                environment.
                            </p>
                        </article>

                        <article>
                            <MessageCircle size={21} />

                            <h3>
                                Technical discussions
                            </h3>

                            <p>
                                Topics may include full-stack architecture,
                                ML inference, model governance, FastAPI,
                                React, PostgreSQL, authentication and
                                healthcare-oriented UX.
                            </p>
                        </article>

                        <article>
                            <BookOpen size={21} />

                            <h3>
                                Research context
                            </h3>

                            <p>
                                The project explores how predictive
                                modelling can be integrated with
                                traceability and clinician oversight rather
                                than presented as an isolated algorithm.
                            </p>
                        </article>
                    </div>
                </section>


                {/* =================================================
            CONTACT NOTICE
            ================================================= */}

                <section className="contact-notice">
                    <ShieldCheck size={22} />

                    <div>
                        <span className="eyebrow">
                            Privacy notice
                        </span>

                        <h3>
                            Please do not submit patient or clinical data.
                        </h3>

                        <p>
                            MEDISCOPE is a synthetic-data prototype.
                            Project enquiries should never include real
                            patient information, confidential health
                            records or other sensitive personal data.
                        </p>
                    </div>
                </section>


                {/* =================================================
            PROJECT QUESTIONS
            ================================================= */}

                <section className="contact-faq-section">
                    <div className="marketing-section-heading">
                        <span className="eyebrow">
                            Common questions
                        </span>

                        <h2 className="section-heading-light">
                            A little more context before you get in touch.
                        </h2>
                    </div>

                    <div className="contact-faq-grid">
                        <article>
                            <h3>
                                Is MEDISCOPE a live clinical system?
                            </h3>

                            <p>
                                No. It is a prototype built for academic,
                                development and demonstration purposes.
                            </p>
                        </article>

                        <article>
                            <h3>
                                Does it use real patient information?
                            </h3>

                            <p>
                                No. The application is designed around
                                synthetic records for demonstration and
                                testing.
                            </p>
                        </article>

                        <article>
                            <h3>
                                Are the ML predictions medical advice?
                            </h3>

                            <p>
                                No. Prediction outputs are decision-support
                                estimates and are explicitly not diagnoses
                                or autonomous treatment decisions.
                            </p>
                        </article>

                        <article>
                            <h3>
                                Can the prototype be demonstrated?
                            </h3>

                            <p>
                                The architecture supports role-specific
                                walkthroughs covering user, clinician and
                                administrator workflows.
                            </p>
                        </article>
                    </div>
                </section>


                {/* =================================================
            CTA
            ================================================= */}

                <section className="simple-page-cta">
                    <div>
                        <span className="eyebrow">
                            Learn more
                        </span>

                        <h2>
                            Explore the purpose, architecture and safety
                            principles behind MEDISCOPE.
                        </h2>
                    </div>

                    <Link
                        className="button primary"
                        to="/about"
                    >
                        About MEDISCOPE
                    </Link>
                </section>
            </main>

            {/* =================================================
                FOOTER
                ================================================= */}

            <footer className="marketing-footer">
                <Brand />

                <p>
                    MEDISCOPE is a synthetic healthcare
                    decision-support prototype. It does not provide
                    medical diagnosis or autonomous clinical
                    decisions.
                </p>

                <nav>
                    <Link to="/">
                        Home
                    </Link>

                    <Link to="/about">
                        About
                    </Link>

                    <Link to="/login">
                        Sign in
                    </Link>
                </nav>
            </footer>
        </div>
    );
}
