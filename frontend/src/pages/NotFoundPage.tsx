import {
    ArrowLeft,
    Compass,
    Home,
    SearchX,
} from 'lucide-react';

import {
    Link,
    useNavigate,
} from 'react-router-dom';

import {
    Brand,
} from '../components/Brand';


export default function NotFoundPage() {
    const navigate =
        useNavigate();

    return (
        <div className="not-found-page">

            {/* =================================================
          BRAND
          ================================================= */}

            <header className="not-found-header">
                <Brand />
            </header>


            {/* =================================================
          CONTENT
          ================================================= */}

            <main className="not-found-content">
                <div className="not-found-icon">
                    <SearchX size={32} />
                </div>

                <span className="not-found-code">
                    404
                </span>

                <span className="eyebrow">
                    Route unavailable
                </span>

                <h1>
                    That page is outside the clinical map.
                </h1>

                <p>
                    The route may have moved, no longer exist, or may
                    not be available within your current MEDISCOPE
                    workflow.
                </p>


                <div className="not-found-actions">
                    <button
                        type="button"
                        className="button secondary"
                        onClick={
                            () =>
                                navigate(
                                    -1,
                                )
                        }
                    >
                        <ArrowLeft size={17} />

                        Go back
                    </button>

                    <Link
                        className="button primary"
                        to="/"
                    >
                        <Home size={17} />

                        Return home
                    </Link>
                </div>


                <div className="not-found-note">
                    <Compass size={16} />

                    <span>
                        If you reached this page from inside MEDISCOPE,
                        use the sidebar to return to an available
                        workspace.
                    </span>
                </div>
            </main>
        </div>
    );
}
