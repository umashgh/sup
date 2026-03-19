import React, { useState } from 'react';
import { IonList, IonItem, IonLabel, IonInput, IonButton, IonSelect, IonSelectOption, IonToast, IonNote } from '@ionic/react';
import api from '../../services/api';
import { formatIndianCurrencyInput } from '../../utils/currency';

interface AssetsFormProps {
    onSave: (data: any) => void;
}

const AssetsForm: React.FC<AssetsFormProps> = ({ onSave }) => {
    const [liquidAssets, setLiquidAssets] = useState(0);
    const [pledgedAssets, setPledgedAssets] = useState(0);
    const [illiquidAssets, setIlliquidAssets] = useState(0);
    const [showToast, setShowToast] = useState(false);
    const [toastMessage, setToastMessage] = useState('');

    const handleSubmit = async () => {
        try {
            // Save Liquid Assets (Personal)
            if (liquidAssets > 0) {
                await api.post('/finance/assets/', {
                    name: 'Personal Liquid Savings',
                    category: 'financial',
                    start_year: new Date().getFullYear(),
                    end_year: new Date().getFullYear() + 20,
                    initial_value: liquidAssets,
                    liquid: true,
                    is_business_pledged: false
                });
            }

            // Save Pledged Assets (Business)
            if (pledgedAssets > 0) {
                await api.post('/finance/assets/', {
                    name: 'Business Capital / Pledged',
                    category: 'financial',
                    start_year: new Date().getFullYear(),
                    end_year: new Date().getFullYear() + 20,
                    initial_value: pledgedAssets,
                    liquid: true,
                    is_business_pledged: true
                });
            }

            // Save Illiquid Assets
            if (illiquidAssets > 0) {
                await api.post('/finance/assets/', {
                    name: 'Real Estate / Gold',
                    category: 'real_estate',
                    start_year: new Date().getFullYear(),
                    end_year: new Date().getFullYear() + 20,
                    initial_value: illiquidAssets,
                    liquid: false,
                    is_business_pledged: false
                });
            }

            onSave({ liquid: liquidAssets, pledged: pledgedAssets, illiquid: illiquidAssets });
        } catch (error) {
            console.error("Error saving assets:", error);
            setToastMessage("Failed to save assets. Please try again.");
            setShowToast(true);
        }
    };

    return (
        <>
            <IonList>
                <IonItem>
                    <IonLabel position="stacked">Personal Liquid Assets (Cash/FDs/Stocks)</IonLabel>
                    <IonInput type="number" value={liquidAssets} onIonChange={e => setLiquidAssets(parseInt(e.detail.value!, 10))} />
                    <IonNote slot="helper">{formatIndianCurrencyInput(liquidAssets)}</IonNote>
                </IonItem>

                <IonItem>
                    <IonLabel position="stacked">Business Capital / Pledged Assets</IonLabel>
                    <IonInput type="number" value={pledgedAssets} onIonChange={e => setPledgedAssets(parseInt(e.detail.value!, 10))} />
                    <IonNote slot="helper">{formatIndianCurrencyInput(pledgedAssets)}</IonNote>
                </IonItem>

                <IonItem>
                    <IonLabel position="stacked">Illiquid Assets (Real Estate/Gold)</IonLabel>
                    <IonInput type="number" value={illiquidAssets} onIonChange={e => setIlliquidAssets(parseInt(e.detail.value!, 10))} />
                    <IonNote slot="helper">{formatIndianCurrencyInput(illiquidAssets)}</IonNote>
                </IonItem>

                <div className="ion-padding">
                    <IonButton expand="block" onClick={handleSubmit}>Calculate Runway</IonButton>
                </div>
            </IonList>
            <IonToast
                isOpen={showToast}
                onDidDismiss={() => setShowToast(false)}
                message={toastMessage}
                duration={3000}
                color="danger"
            />
        </>
    );
};

export default AssetsForm;
