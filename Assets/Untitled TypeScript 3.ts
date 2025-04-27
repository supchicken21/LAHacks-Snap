@component
export default class NewScript extends BaseScriptComponent {
    private remoteServiceModule: any = require("LensStudio:RemoteServiceModule");
    @input
    kunais: ObjectPrefab[];

    @input
    kunaiSO: SceneObject[];

    @input
    maxTurns: number = 5;        // How many resets before disabling

    @input
    cameraObject: SceneObject; // Camera's physics collider

    @input
    textComponent: Text3D;

    private transforms: Transform[] = [];
    private initialPositions: vec3[] = [];
    private turnCounters: number[] = [];
    private visibleKunais: boolean[] = [];
    private bodies: any[] = [];            // Using 'any' since Lens Studio TS lacks Physics.BodyComponent type
    private speeds: number[] = [];
    private respawnDelay: number[] = [];
    private respawnTimer: number[] = [];
    private cameraColliderComponent: any;
    private respawnedKunais: number = 0;
    private cycleCount: number = 0;
    private collisionCountFirstThird: number = 0;
    private collisionCountSecondThird: number = 0;
    private collisionCountThirdThird: number = 0;
    
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
            this.speeds[i] = Math.random() * 15 + 5; 
            this.respawnDelay[i] = Math.random() * 1 + 1;
            this.respawnTimer[i] = 0;
          }
      
          this.createEvent("UpdateEvent").bind(this.update.bind(this));
        }
      
        async update(eventData: { getDeltaTime(): number }) {
          const dt = eventData.getDeltaTime();
          const totalTurns = this.maxTurns * this.kunais.length;
          const firstThirdThreshold = totalTurns / 3;
          const secondThirdThreshold = 2 * totalTurns / 3;
      
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
                this.speeds[i] = Math.random() * 30 + 5;
                this.respawnTimer[i] = 0;
                this.respawnDelay[i] = Math.random() * 1 + 1; // New random delay
                this.respawnedKunais++;

                if (this.respawnedKunais === this.kunais.length) {
                    print("Cycle " + this.cycleCount + " Complete!");
                    this.cycleCount++;
                    
                    // Increment collision counters
                    const collisionMatch = this.textComponent.text.match(/Collisions: (\d+)/);
                    if (collisionMatch) {
                        const collisionCount = parseInt(collisionMatch[1]);
                        if (this.cycleCount <= firstThirdThreshold) {
                            this.collisionCountFirstThird += collisionCount;
                        } else if (this.cycleCount <= secondThirdThreshold) {
                            this.collisionCountSecondThird += collisionCount;
                        } else {
                            this.collisionCountThirdThird += collisionCount;
                        }
                    }

                    this.respawnedKunais = 0;
                }
              }
            } else {
              this.respawnTimer[i] = 0; // Reset timer if not at end
            }
      
            if (this.turnCounters[i] >= this.maxTurns) {
              this.visibleKunais[i] = false;
              this.kunaiSO[i].enabled = false;
            }
          }

        let allKunaisInvisible = true;
        for (let i = 0; i < this.kunais.length; i++) {
            if (this.visibleKunais[i]) {
                allKunaisInvisible = false;
                break;
            }
        }

        if (allKunaisInvisible) {
            this.sendData();
        }
    }

    private hasSentData: boolean = false;

    async sendData() {
        if (this.hasSentData) {
            return;
        }

        if (this.textComponent) {
            print("All cycles complete!" + this.textComponent.text);

            const url = "https://0d83-164-67-70-232.ngrok-free.app/submit_game_data";
            const headers = {
                "Content-Type": "application/json"
            };
            const body = JSON.stringify({
                "date": getTime(),
                "Collisions" : this.textComponent.text,
                "Total Kunais" : 4 * this.maxTurns,
                "collisionsFirstThird": this.collisionCountFirstThird,
                "collisionsSecondThird": this.collisionCountSecondThird,
                "collisionsThirdThird": this.collisionCountThirdThird,
            });

            const request = new Request(url, {
                method: "POST",
                headers: headers,
                body: body
            });

            try {
                const response = await this.remoteServiceModule.fetch(request);
                print("Response:" + response.status);
            } catch (error) {
                print("Error:" + error);
            }

            this.hasSentData = true;
        }
    }
}
