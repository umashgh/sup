import React, { useState } from 'react';
import { IonList, IonItem, IonLabel, IonInput, IonSelect, IonSelectOption, IonButton, IonToast } from '@ionic/react';
import api from '../../services/api';

interface VentureFormProps {
    onSave: (data: any) => void;
}

const VentureForm: React.FC<VentureFormProps> = ({ onSave }) => {
    const [name, setName] = useState('');
    const [stage, setStage] = useState('idea');
    const [runway, setRunway] = useState(12);
    const [showToast, setShowToast] = useState(false);
    const [toastMessage, setToastMessage] = useState('');

    const handleSubmit = async () => {
        try {
            const response = await api.post('/ventures/ventures/', {
                name,
                stage,
                target_runway_months: runway
            });
            onSave(response.data);
        } catch (error) {
            console.error("Error saving venture:", error);
            setToastMessage("Failed to save venture. Please try again.");
            setShowToast(true);
        }
    };

    return (
        <>
            <IonList>
                <IonItem>
                    <IonLabel position="stacked">Venture Name</IonLabel>
                    <IonInput value={name} onIonChange={e => setName(e.detail.value!)} placeholder="My Awesome Startup" />
                </IonItem>

                <IonItem>
                    <IonLabel position="stacked">Stage</IonLabel>
                    <IonSelect value={stage} onIonChange={e => setStage(e.detail.value)}>
                        <IonSelectOption value="idea">Idea</IonSelectOption>
                        <IonSelectOption value="mvp">MVP</IonSelectOption>
                        <IonSelectOption value="growth">Growth</IonSelectOption>
                    </IonSelect>
                </IonItem>

                <IonItem>
                    <IonLabel position="stacked">Target Runway (Months)</IonLabel>
                    <IonInput type="number" value={runway} onIonChange={e => setRunway(parseInt(e.detail.value!, 10))} />
                </IonItem>

                <div className="ion-padding">
                    <IonButton expand="block" onClick={handleSubmit}>Save & Continue</IonButton>
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

export default VentureForm;
