import React from 'react';
import { IonContent, IonHeader, IonPage, IonTitle, IonToolbar } from '@ionic/react';
import StoryContainer from '../components/StoryContainer';

const Home: React.FC = () => {
  return (
    <IonPage>
      <IonHeader>
        <IonToolbar>
          <IonTitle>Founder FIRE</IonTitle>
        </IonToolbar>
      </IonHeader>
      <IonContent fullscreen className="ion-padding">
        <IonHeader collapse="condense">
          <IonToolbar>
            <IonTitle size="large">Founder FIRE</IonTitle>
          </IonToolbar>
        </IonHeader>

        <StoryContainer />

      </IonContent>
    </IonPage>
  );
};

export default Home;
