import React from 'react';
import { IonCard, IonCardHeader, IonCardTitle, IonCardContent, IonIcon } from '@ionic/react';
import { checkmarkCircle, lockClosed } from 'ionicons/icons';
import { motion, AnimatePresence } from 'framer-motion';

interface StoryCardProps {
    title: string;
    status: 'locked' | 'active' | 'completed';
    children: React.ReactNode;
    summary?: React.ReactNode;
}

const StoryCard: React.FC<StoryCardProps> = ({ title, status, children, summary }) => {
    const isLocked = status === 'locked';
    const isCompleted = status === 'completed';
    const isActive = status === 'active';

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: isLocked ? 0.5 : 1, y: 0 }}
            transition={{ duration: 0.5 }}
        >
            <IonCard className={isActive ? 'active-card' : ''} disabled={isLocked}>
                <IonCardHeader>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <IonCardTitle>{title}</IonCardTitle>
                        {isCompleted && <IonIcon icon={checkmarkCircle} color="success" size="large" />}
                        {isLocked && <IonIcon icon={lockClosed} color="medium" size="large" />}
                    </div>
                </IonCardHeader>

                <AnimatePresence>
                    {isActive && (
                        <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.5 }}
                        >
                            <IonCardContent>
                                {children}
                            </IonCardContent>
                        </motion.div>
                    )}
                </AnimatePresence>

                {isCompleted && summary && (
                    <IonCardContent>
                        <div style={{ opacity: 0.8 }}>
                            {summary}
                        </div>
                    </IonCardContent>
                )}
            </IonCard>
        </motion.div>
    );
};

export default StoryCard;
