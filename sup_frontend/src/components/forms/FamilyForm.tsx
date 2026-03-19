import React, { useState, useEffect } from 'react';
import { IonList, IonItem, IonLabel, IonInput, IonButton, IonSelect, IonSelectOption, IonToast, IonIcon, IonListHeader, IonRange } from '@ionic/react';
import { trashOutline, addCircleOutline } from 'ionicons/icons';
import api, { fetchFamilyMembers, addFamilyMember, deleteFamilyMember, calculateDefaults, fetchFamilyProfile } from '../../services/api';

interface FamilyFormProps {
    onSave: (data: any) => void;
}

const FamilyForm: React.FC<FamilyFormProps> = ({ onSave }) => {
    const [wealthLevel, setWealthLevel] = useState(1);
    const [incomeLevel, setIncomeLevel] = useState(1);
    const [expenseLevel, setExpenseLevel] = useState(1);
    
    // Budget Splits
    const [needsPercent, setNeedsPercent] = useState(50);
    const [wantsPercent, setWantsPercent] = useState(30);
    // Savings is derived: 100 - needs - wants

    const [showToast, setShowToast] = useState(false);
    const [toastMessage, setToastMessage] = useState('');
    
    const [members, setMembers] = useState<any[]>([]);
    const [newMemberName, setNewMemberName] = useState('');
    const [newMemberType, setNewMemberType] = useState('earning_adult');
    const [newMemberAge, setNewMemberAge] = useState<number | string>('');

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        try {
            const membersData = await fetchFamilyMembers();
            setMembers(membersData);
            
            const profiles = await fetchFamilyProfile();
            if (profiles.length > 0) {
                const p = profiles[0];
                setWealthLevel(p.wealth_level);
                setIncomeLevel(p.income_level);
                setExpenseLevel(p.expense_level);
                setNeedsPercent(p.needs_percent);
                setWantsPercent(p.wants_percent);
            }
        } catch (e) {
            console.error("Failed to load data", e);
        }
    };

    const updateDefaults = async () => {
        try {
            const profiles = await fetchFamilyProfile();
            if (profiles.length > 0) {
                const updatedProfile = await calculateDefaults(profiles[0].id);
                setNeedsPercent(updatedProfile.needs_percent);
                setWantsPercent(updatedProfile.wants_percent);
                setToastMessage("Budget splits updated based on family profile");
                setShowToast(true);
            }
        } catch (e) {
            console.error("Failed to update defaults", e);
        }
    };

    const handleAddMember = async () => {
        if (!newMemberName || !newMemberAge) {
            setToastMessage("Please enter name and age");
            setShowToast(true);
            return;
        }
        try {
            await addFamilyMember({
                name: newMemberName,
                member_type: newMemberType,
                age: parseInt(newMemberAge.toString(), 10)
            });
            setNewMemberName('');
            setNewMemberAge('');
            
            // Reload members and update defaults
            const membersData = await fetchFamilyMembers();
            setMembers(membersData);
            await updateDefaults();
            
        } catch (e) {
            console.error("Failed to add member", e);
            setToastMessage("Failed to add member");
            setShowToast(true);
        }
    };

    const handleDeleteMember = async (id: number) => {
        try {
            await deleteFamilyMember(id);
            
            // Reload members and update defaults
            const membersData = await fetchFamilyMembers();
            setMembers(membersData);
            await updateDefaults();
            
        } catch (e) {
            console.error("Failed to delete member", e);
        }
    };

    const handleSubmit = async () => {
        try {
            const savingsPercent = 100 - needsPercent - wantsPercent;
            if (savingsPercent < 0) {
                setToastMessage("Total percentage cannot exceed 100%");
                setShowToast(true);
                return;
            }

            const profiles = await api.get('/finance/profile/');
            if (profiles.data.length > 0) {
                const id = profiles.data[0].id;
                const response = await api.patch(`/finance/profile/${id}/`, {
                    wealth_level: wealthLevel,
                    income_level: incomeLevel,
                    expense_level: expenseLevel,
                    needs_percent: needsPercent,
                    wants_percent: wantsPercent,
                    savings_percent: savingsPercent
                });
                
                // Trigger default calculation on backend if needed, or just save
                // For now we just save what user selected
                
                onSave({ ...response.data, members });
            } else {
                throw new Error("No profile found");
            }
        } catch (error) {
            console.error("Error saving family profile:", error);
            setToastMessage("Failed to save family profile. Please try again.");
            setShowToast(true);
        }
    };

    return (
        <>
            <IonList>
                <IonListHeader>
                    <IonLabel>Family Profile Levels</IonLabel>
                </IonListHeader>
                <IonItem>
                    <IonLabel position="stacked">Wealth Level (Assets)</IonLabel>
                    <IonSelect value={wealthLevel} onIonChange={e => setWealthLevel(e.detail.value)}>
                        <IonSelectOption value={1}>Level 1 (&lt; 2 Cr)</IonSelectOption>
                        <IonSelectOption value={2}>Level 2 (2-10 Cr)</IonSelectOption>
                        <IonSelectOption value={3}>Level 3 (&gt; 10 Cr)</IonSelectOption>
                    </IonSelect>
                </IonItem>

                <IonItem>
                    <IonLabel position="stacked">Income Level (Annual)</IonLabel>
                    <IonSelect value={incomeLevel} onIonChange={e => setIncomeLevel(e.detail.value)}>
                        <IonSelectOption value={1}>Level 1 (&lt; 20 L)</IonSelectOption>
                        <IonSelectOption value={2}>Level 2 (20-50 L)</IonSelectOption>
                        <IonSelectOption value={3}>Level 3 (&gt; 50 L)</IonSelectOption>
                    </IonSelect>
                </IonItem>

            <IonItem>
                <IonLabel position="stacked">Expense Level (Annual)</IonLabel>
                <IonSelect value={expenseLevel} onIonChange={e => setExpenseLevel(e.detail.value)}>
                    <IonSelectOption value={1}>Level 1 (&lt; 20 L)</IonSelectOption>
                    <IonSelectOption value={2}>Level 2 (20-50 L)</IonSelectOption>
                    <IonSelectOption value={3}>Level 3 (&gt; 50 L)</IonSelectOption>
                </IonSelect>
            </IonItem>

            <IonListHeader>
                <IonLabel>Budget Allocation (Smart Defaults)</IonLabel>
            </IonListHeader>
            <IonItem>
                <IonLabel position="stacked">Needs (Survival): {needsPercent}%</IonLabel>
                <IonRange min={0} max={100} value={needsPercent} onIonChange={e => setNeedsPercent(e.detail.value as number)} color="danger">
                    <IonLabel slot="start">0%</IonLabel>
                    <IonLabel slot="end">100%</IonLabel>
                </IonRange>
            </IonItem>
            <IonItem>
                <IonLabel position="stacked">Wants (Lifestyle): {wantsPercent}%</IonLabel>
                <IonRange min={0} max={100 - needsPercent} value={wantsPercent} onIonChange={e => setWantsPercent(e.detail.value as number)} color="warning">
                    <IonLabel slot="start">0%</IonLabel>
                    <IonLabel slot="end">{100 - needsPercent}%</IonLabel>
                </IonRange>
            </IonItem>
            <IonItem>
                <IonLabel>Savings/Investments: {100 - needsPercent - wantsPercent}%</IonLabel>
            </IonItem>

            <IonListHeader>
                <IonLabel>Family Members</IonLabel>
            </IonListHeader>                {members.map(member => (
                    <IonItem key={member.id}>
                        <IonLabel>
                            <h2>{member.name}</h2>
                            <p>{member.member_type} - {member.age} yrs</p>
                        </IonLabel>
                        <IonButton fill="clear" color="danger" slot="end" onClick={() => handleDeleteMember(member.id)}>
                            <IonIcon icon={trashOutline} />
                        </IonButton>
                    </IonItem>
                ))}

                <IonItem>
                    <IonInput 
                        placeholder="Name" 
                        value={newMemberName} 
                        onIonChange={e => setNewMemberName(e.detail.value!)} 
                    />
                </IonItem>
                <IonItem>
                    <IonInput 
                        type="number" 
                        placeholder="Age" 
                        value={newMemberAge} 
                        onIonChange={e => setNewMemberAge(e.detail.value!)} 
                    />
                </IonItem>
                <IonItem>
                    <IonSelect value={newMemberType} onIonChange={e => setNewMemberType(e.detail.value)}>
                        <IonSelectOption value="earning_adult">Earning Adult</IonSelectOption>
                        <IonSelectOption value="dependent_adult">Dependent Adult</IonSelectOption>
                        <IonSelectOption value="child">Child</IonSelectOption>
                        <IonSelectOption value="pet">Pet</IonSelectOption>
                    </IonSelect>
                </IonItem>
                <IonButton expand="block" fill="outline" onClick={handleAddMember} className="ion-margin">
                    <IonIcon slot="start" icon={addCircleOutline} />
                    Add Member
                </IonButton>

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

export default FamilyForm;
