@component
export default class CollisionCounter extends BaseScriptComponent {
    @input
    cameraObject: SceneObject;

    @input
    kunais: SceneObject[];

    public counter: number = -1;

    @input
    private cameraColliderComponent: ColliderComponent;
    
    @input
    private textComponent: Text3D;

    private lastCollider: ColliderComponent | null = null;

    onAwake() {
        this.cameraColliderComponent.onOverlapEnter.add(() => {
                this.incrementCounter();
            })
    }

    public incrementCounter() {
        this.counter++;
        print("Counter: " + this.counter);
        if (this.textComponent) {
            this.textComponent.text = "Collisions: " + this.counter;
        }
    }
}