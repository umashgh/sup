import React, { useState, useEffect } from 'react';
import { IonSpinner, IonToggle, IonRange, IonLabel, IonItem, IonList } from '@ionic/react';
import StoryCard from './StoryCard';
import { guestLogin, fetchProjection, setAuthToken, fetchFamilyProfile } from '../services/api';
import VentureForm from './forms/VentureForm';
import FamilyForm from './forms/FamilyForm';
import AssetsForm from './forms/AssetsForm';
import FinancialHealthGraph from './FinancialHealthGraph';
import { formatIndianCurrency } from '../utils/currency';

const StoryContainer: React.FC = () => {
    const [loading, setLoading] = useState(true);
    const [step, setStep] = useState(0);
    const [ventureData, setVentureData] = useState<any>(null);
    const [familyData, setFamilyData] = useState<any>(null);
    const [assetsData, setAssetsData] = useState<any>(null);

    const [projectionData, setProjectionData] = useState<any[]>([]);
    
    // Runway Config
    const [austerityMode, setAusterityMode] = useState(false);
    const [emergencyMonths, setEmergencyMonths] = useState(6);

    useEffect(() => {
        const init = async () => {
            try {
                const token = localStorage.getItem('token');
                if (token) {
                    setAuthToken(token);
                    try {
                        // Validate token by making a request
                        await fetchFamilyProfile();
                    } catch (e: any) {
                        // If 401, the interceptor might have already cleared the token
                        // But we explicitly handle re-login here
                        console.log("Token invalid, re-logging in as guest...");
                        await guestLogin();
                    }
                } else {
                    await guestLogin();
                }
                setLoading(false);
            } catch (e) {
                console.error("Initialization error:", e);
                // If guest login fails, we might want to retry or show error
                // For now, just stop loading so user sees something (maybe broken state but better than spinner)
                setLoading(false);
            }
        };
        init();
    }, []);

    useEffect(() => {
        if (step >= 3) {
            updateProjection();
        }
    }, [austerityMode, emergencyMonths]);

    const updateProjection = async () => {
        try {
            const proj = await fetchProjection(austerityMode, emergencyMonths);
            setProjectionData(proj);
        } catch (e) {
            console.error("Failed to fetch projection", e);
        }
    };

    const nextStep = () => setStep(s => s + 1);

    const handleVentureSave = (data: any) => {
        setVentureData(data);
        nextStep();
    };

    const handleFamilySave = (data: any) => {
        setFamilyData(data);
        nextStep();
    };

    const handleAssetsSave = async (data: any) => {
        setAssetsData(data);
        await updateProjection();
        nextStep();
    };

    if (loading) {
        return (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
                <IonSpinner />
            </div>
        );
    }

    return (
        <div style={{ paddingBottom: '100px' }}>
            {/* Step 0: Welcome / Venture Info */}
            <StoryCard
                title="Your Venture"
                status={step === 0 ? 'active' : (step > 0 ? 'completed' : 'locked')}
                summary={<p>Venture: <strong>{ventureData?.name || 'Saved'}</strong></p>}
            >
                <p>Tell us about your new business idea.</p>
                <VentureForm onSave={handleVentureSave} />
            </StoryCard>

            {/* Step 1: Family Profile */}
            <StoryCard
                title="Family Profile"
                status={step === 1 ? 'active' : (step > 1 ? 'completed' : 'locked')}
                summary={<p>Family Profile Saved</p>}
            >
                <p>Who depends on you?</p>
                <FamilyForm onSave={handleFamilySave} />
            </StoryCard>

            {/* Step 2: Assets */}
            <StoryCard
                title="Assets & Runway"
                status={step === 2 ? 'active' : (step > 2 ? 'completed' : 'locked')}
                summary={<p>Assets Saved</p>}
            >
                <p>What's your safety net?</p>
                <AssetsForm onSave={handleAssetsSave} />
            </StoryCard>

            {/* Step 3: Results */}
            {step >= 3 && (
                <StoryCard
                    title="Financial Projection"
                    status="active"
                    summary={<p>Projection Ready</p>}
                >
                    <p>Here is how your finances look over the next 20 years.</p>
                    
                    <IonList className="ion-margin-bottom">
                        <IonItem>
                            <IonLabel>Austerity Mode (Cut Wants 50%)</IonLabel>
                            <IonToggle checked={austerityMode} onIonChange={e => setAusterityMode(e.detail.checked)} />
                        </IonItem>
                        <IonItem>
                            <IonLabel position="stacked">Emergency Fund: {emergencyMonths} Months</IonLabel>
                            <IonRange min={0} max={24} value={emergencyMonths} onIonChange={e => setEmergencyMonths(e.detail.value as number)}>
                                <IonLabel slot="start">0</IonLabel>
                                <IonLabel slot="end">24</IonLabel>
                            </IonRange>
                        </IonItem>
                    </IonList>

                    <FinancialHealthGraph data={projectionData} />
                    {projectionData.length > 0 && projectionData[0].pledged_assets > 0 && (
                        <p style={{ color: '#d9534f', fontSize: '0.9em', marginTop: '10px' }}>
                            Note: {formatIndianCurrency(projectionData[0].pledged_assets)} is pledged to your business and excluded from this projection.
                        </p>
                    )}
                    <p style={{ marginTop: '10px', fontSize: '0.9em', color: '#666' }}>
                        This is a preliminary projection based on your inputs.
                    </p>
                </StoryCard>
            )}
        </div>
    );
};

export default StoryContainer;
