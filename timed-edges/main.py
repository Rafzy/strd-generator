entities = []
packets = []

difficulty_level = 1

# Assign packets to entities randomly with rules

ground_truth = []
event_timeline = []
trg_obj = sample(packets)


states = State()

for i in range 10:
    stamp = generate_timestamp()
    action = sample_action()
    event_timeline.append(action)
    states.update_state(action)
