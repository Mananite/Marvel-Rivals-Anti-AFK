import time
import random
import threading
import vgamepad as vg
import keyboard  # pip install keyboard

# Inicializar mando virtual DS4
gamepad = vg.VDS4Gamepad()

# Estado del toggle
enabled = False
special_pending = False
special_lock = threading.Lock()
ready_for_special = False  # Solo se activa después de centrar el stick izquierdo
Test_Time_Divide_By_E = 1 #Can't be arsed to wait a whole ass 2 mins for 1 test that's gonna fucking fail
Test_Time_Divide_By_Move = 2 #Can't be arsed to wait a whole ass 2 mins for 1 test that's gonna fucking fail

def toggle_listener():
    global enabled
    while True:
        keyboard.wait("right")
        enabled = not enabled
        print(f"[TOGGLE] Script {'activado' if enabled else 'desactivado'}")
        time.sleep(0.3)  # evitar rebotes

def press_button(btn, duration, name=""):
    print(f"[ACTION] Pulsando {name} durante {duration:.2f}s")
    gamepad.press_button(button=btn)
    gamepad.update()
    time.sleep(duration)
    gamepad.release_button(button=btn)
    gamepad.update()

def move_stick_smooth(y_target, move_time=None, steps=8, stick="left", description=""):
    if move_time is None:
        move_time = random.uniform(0.1, 0.2)  # más rápido

    print(f"[ACTION] Moviendo stick {stick} hacia {description} en {move_time:.2f}s")
    for i in range(steps):
        fraction = (i + 1) / steps
        jitter = random.uniform(-0.03, 0.03)
        y_value = max(-1.0, min(1.0, (y_target * fraction) + jitter))
        if stick == "left":
            gamepad.left_joystick_float(x_value_float=0.0, y_value_float=y_value)
        elif stick == "right":
            gamepad.right_joystick_float(x_value_float=0.0, y_value_float=y_value)
        gamepad.update()
        time.sleep(move_time / steps)

def center_stick(stick="left", move_time=None, steps=4):
    """Centra el stick suavemente en ~0.09s ± 0.01s con jitter"""
    global ready_for_special
    if move_time is None:
        move_time = random.uniform(0.08, 0.10)
    print(f"[ACTION] Centrado rápido stick {stick} en {move_time:.2f}s")

    for i in range(steps):
        jitter = random.uniform(-0.02, 0.02)
        y_value = max(-1.0, min(1.0, 0.0 + jitter))
        if stick == "left":
            gamepad.left_joystick_float(x_value_float=0.0, y_value_float=y_value)
        elif stick == "right":
            gamepad.right_joystick_float(x_value_float=0.0, y_value_float=y_value)
        gamepad.update()
        time.sleep(move_time / steps)

    if stick == "left":
        ready_for_special = True  # listo para special action

def e_task():
    global enabled, special_pending
    while True:
        if enabled:
            wait_time = random.uniform(14, 30)/Test_Time_Divide_By_E
            print(f"[WAIT] Esperando {wait_time:.2f}s antes de pulsar R1")
            time.sleep(wait_time)
            duration = random.uniform(0.6, 1.35)
            press_button(vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT, duration, name="R1 (antes E)")

            # Delay extra si se acaba de ejecutar special
            with special_lock:
                if special_pending:
                    print("[DELAY] 10s adicionales tras Special Action")
                    time.sleep(10)
                    special_pending = False
        else:
            time.sleep(0.1)

def ws_task():
    global enabled, special_pending, ready_for_special
    while True:
        if enabled:
            wait_time = random.uniform(15, 46)/Test_Time_Divide_By_Move
            print(f"[WAIT] Esperando {wait_time:.2f}s antes de mover W/S")
            time.sleep(wait_time)

            w_duration = random.uniform(0.1, 0.3)
            move_stick_smooth(1.0, stick="left", description="arriba (W)")
            time.sleep(w_duration)
            center_stick(stick="left")

            if w_duration == 0.1:
                w_duration = 0.2
            pause_time = random.uniform(0.2, 0.7)
            print(f"[WAIT] Pausa entre W y S: {pause_time:.2f}s")
            time.sleep(pause_time)

            s_duration = max(0, w_duration + random.uniform(-0.1, 0.1))
            move_stick_smooth(-1.0, stick="left", description="abajo (S)")
            time.sleep(s_duration)
            center_stick(stick="left")

            # Solo después de centrar stick, 55% probabilidad de special action
            if ready_for_special and random.random() < 0.55:
                with special_lock:
                    special_pending = True
                ready_for_special = False
        else:
            time.sleep(0.1)

def special_action_task():
    global enabled, special_pending
    execute = True
    while True:
        if enabled:
            execute = False
            with special_lock:
                if special_pending:
                    execute = True
                    special_pending = False
            if execute:
                wait_time = random.uniform(1, 1.5)
                print(f"[WAIT] Esperando {wait_time:.2f}s antes de acción especial")
                time.sleep(wait_time)

                print("[SPECIAL] Manteniendo D-pad derecha + R1 y mirando arriba")
                gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_WEST)
                time.sleep(0.2)
                move_stick_smooth(1.0, move_time=0.15, stick="right", description="arriba (mirar)")

                hold_time = random.uniform(0.7, 1.2)
                print(f"[SPECIAL] Manteniendo posición durante {hold_time:.2f}s")
                time.sleep(hold_time)

                center_stick(stick="right", move_time=0.15)
                gamepad.release_button(button=vg.DS4_BUTTONS.DS4_BUTTON_SHOULDER_RIGHT)
                gamepad.directional_pad(direction=vg.DS4_DPAD_DIRECTIONS.DS4_BUTTON_DPAD_NONE)
                gamepad.update()
            else:
                time.sleep(0.1)
        else:
            time.sleep(0.1)

if __name__ == "__main__":
    threading.Thread(target=toggle_listener, daemon=True).start()
    threading.Thread(target=e_task, daemon=True).start()
    threading.Thread(target=ws_task, daemon=True).start()
    threading.Thread(target=special_action_task, daemon=True).start()

    print("Controlador PS4 virtual activo. Pulsa flecha derecha para activar/desactivar.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Finalizando...")
        center_stick(stick="left")
        center_stick(stick="right")
