@component
export default class NewScript extends BaseScriptComponent {
    @input()
    kunais: ObjectPrefab[];

    @input
    kunaiSO: SceneObject[];

    @input()
    maxTurns: number = 5;        // How many resets before disabling

    @input()
    cameraObject: SceneObject; // Camera's physics collider

    private transforms: Transform[] = [];
    private initialPositions: vec3[] = [];
    private turnCounters: number[] = [];
    private visibleKunais: boolean[] = [];
    private bodies: any[] = [];            // Using 'any' since Lens Studio TS lacks Physics.BodyComponent type
    private speeds: number[] = [];
    private respawnDelay: number[] = [];
    private respawnTimer: number[] = [];
    private cameraColliderComponent: any;
    private beginningThird: number = 0;
    private middleThird: number = 0;
    private bottomThird: number = 0;
    onAwake() {

    }
    generate(){
        if (this.cameraObject) {
            this.cameraColliderComponent = this.cameraObject.getComponent("Physics.ColliderComponent");
          }
      
          for (let i = 0; i < this.kunaiSO.length; i++) {
            const kunai = this.kunaiSO[i];
            this.transforms[i] = kunai.getTransform();
            this.initialPositions[i] = this.transforms[i].getLocalPosition();
            this.turnCounters[i] = 0;
            this.visibleKunais[i] = true;
            this.bodies[i] = kunai.getComponent("Physics.BodyComponent");
            this.speeds[i] = Math.random() * 15 + 5; // Random speed between 25 and 75
            this.respawnDelay[i] = Math.random() * 1 + 1; // Random delay between 1 and 3 seconds
            this.respawnTimer[i] = 0;
          }
      
          this.createEvent("UpdateEvent").bind(this.update.bind(this));
        }
      
        update(eventData: { getDeltaTime(): number }) {
          const dt = eventData.getDeltaTime();
      
          for (let i = 0; i < this.kunais.length; i++) {
            if (!this.visibleKunais[i] || this.turnCounters[i] >= this.maxTurns) {
              continue;
            }
      
            const pos = this.transforms[i].getLocalPosition();
            pos.z += dt * this.speeds[i];
            this.transforms[i].setLocalPosition(pos);
      
            if (pos.z > 40) {
              this.respawnTimer[i] += dt;
      
              if (this.respawnTimer[i] > this.respawnDelay[i]) {
                this.transforms[i].setLocalPosition(this.initialPositions[i]);
                this.kunaiSO[i].enabled = true;
                this.turnCounters[i]++;
                this.speeds[i] = Math.random() * 30 + 5; // New random speed between 25 and 75
                this.respawnTimer[i] = 0;
                this.respawnDelay[i] = Math.random() * 2 + 1; // New random delay
              }
            } else {
              this.respawnTimer[i] = 0; // Reset timer if not at end
            }
      
            if (this.turnCounters[i] >= this.maxTurns) {
              this.visibleKunais[i] = false;
              this.kunaiSO[i].enabled = false;
            }
          }
    }
    
    
}
