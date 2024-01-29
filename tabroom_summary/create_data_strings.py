def create_data_strings(data_objects, data_labels):
    data_strings_all = []
    for data_object in data_objects:
        data_object_filtered = []
        for data_label in data_labels:
            if data_label in data_object.keys():
                try:
                    if isinstance(data_object[data_label], list):
                        data_object_filtered.append("!".join(data_object[data_label]))
                    elif isinstance(data_object[data_label], (int, float)):
                        data_object_filtered.append(str(data_object[data_label]))
                    else:
                        data_object_filtered.append(data_object[data_label])
                except:
                    data_object_filtered.append("N/A")
            else:
                data_object_filtered.append("N/A")
        data_strings_all.append("|".join(data_object_filtered))
    return data_strings_all


if __name__ == "__main__":
    print(
        create_data_strings(
            data_objects=[
                {"name": "John", "age": 30, "city": "New York"},
                {"name": "Jane", "age": 25, "city": "Chicago"},
            ],
            data_labels=["name", "age", "city"],
        )
    )
    data_objects = [
        {
            "event_name": "Lincoln Douglas",
            "event_type": "debate",
            "label": 4,
            "entry_name": "Angela Davaasambuu",
            "entry_code": "213",
            "school_name": "Mira Loma",
            "round_reached": "N/A",
            "percentile": -1,
            "win_loss": "1W3L",
            "results_by_round": [
                "Round 1: W ",
                "Round 2: L ",
                "Round 3: L ",
                "Round 4: L ",
            ],
        }
    ]
    data_labels = [
        "event_name",
        "event_type",
        "results_by_round",
    ]
    print(create_data_strings(data_objects, data_labels))
