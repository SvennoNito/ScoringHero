"""Tests for the Events module: 13 Event slots, edit operations and derived Event epochs.
Plain numbers only, no Qt, no session object."""

import pytest

from scoring_model.events import ARTEFACT_SLOT, N_SLOTS, Events


def make(epoch_length_s=30, n_epochs=10):
    return Events(epoch_length_s, n_epochs)


def test_thirteen_slots_identified_by_position():
    ev = make()
    assert N_SLOTS == 13
    assert ARTEFACT_SLOT == 0
    assert [ev.spans(s) for s in range(N_SLOTS)] == [[] for _ in range(13)]
    with pytest.raises(IndexError):
        ev.spans(13)
    with pytest.raises(IndexError):
        ev.add(-1, [(0, 1)])


def test_default_labels_and_colours_per_slot():
    ev = make()
    assert ev.label(0) == "Artifact"
    assert ev.label(5) == "F5"
    colours = [ev.colour(s) for s in range(N_SLOTS)]
    assert all(len(c) == 4 for c in colours)
    assert len(set(colours)) == N_SLOTS


def test_duplicate_labels_allowed_and_slot_stays_the_identity():
    ev = make()
    ev.set_label(1, "Spindle")
    ev.set_label(2, "Spindle")
    ev.add(2, [(5, 8)])
    assert ev.label(1) == ev.label(2) == "Spindle"
    assert ev.spans(1) == []
    assert ev.spans(2) == [[5, 8]]


def test_add_keeps_spans_ordered_and_merges_overlapping():
    ev = make()
    ev.add(3, [(50, 60), (10, 20), (15, 30)])
    assert ev.spans(3) == [[10, 30], [50, 60]]


def test_add_merges_touching_spans():
    ev = make()
    ev.add(3, [(10, 20)])
    ev.add(3, [(20, 30)])
    assert ev.spans(3) == [[10, 30]]


def test_add_ignores_empty_and_reversed_spans():
    ev = make()
    ev.add(3, [(10, 10), (30, 20)])
    assert ev.spans(3) == []


def test_spans_returns_a_copy():
    ev = make()
    ev.add(3, [(10, 20)])
    ev.spans(3)[0][1] = 99
    assert ev.spans(3) == [[10, 20]]


def test_slots_are_independent():
    ev = make()
    ev.add(1, [(10, 20)])
    ev.add(2, [(15, 25)])
    assert ev.spans(1) == [[10, 20]]
    assert ev.spans(2) == [[15, 25]]


# ---- toggle epoch -----------------------------------------------------------


def test_toggle_epoch_adds_an_absent_epoch():
    ev = make()
    ev.toggle_epoch(3, 2)
    assert ev.spans(3) == [[60, 90]]


def test_toggle_epoch_removes_an_exact_epoch_event():
    ev = make()
    ev.add(3, [(60, 90)])
    ev.toggle_epoch(3, 2)
    assert ev.spans(3) == []


def test_toggle_epoch_twice_restores_the_slot():
    ev = make()
    ev.add(3, [(5, 10)])
    ev.toggle_epoch(3, 4)
    ev.toggle_epoch(3, 4)
    assert ev.spans(3) == [[5, 10]]


def test_toggle_epoch_splits_a_containing_event():
    ev = make()
    ev.add(3, [(30, 150)])
    ev.toggle_epoch(3, 2)
    assert ev.spans(3) == [[30, 60], [90, 150]]


def test_toggle_epoch_removes_the_epoch_at_the_edge_of_an_event():
    ev = make()
    ev.add(3, [(30, 90)])
    ev.toggle_epoch(3, 1)
    assert ev.spans(3) == [[60, 90]]


def test_toggle_epoch_extends_a_partially_covering_event():
    ev = make()
    ev.add(3, [(10, 40)])
    ev.toggle_epoch(3, 1)
    assert ev.spans(3) == [[10, 60]]


def test_toggle_epoch_merges_with_adjacent_event():
    ev = make()
    ev.add(3, [(30, 60)])
    ev.toggle_epoch(3, 2)
    assert ev.spans(3) == [[30, 90]]


def test_toggle_epoch_only_touches_its_slot():
    ev = make()
    ev.add(1, [(60, 90)])
    ev.toggle_epoch(2, 2)
    assert ev.spans(1) == [[60, 90]]
    assert ev.spans(2) == [[60, 90]]


def test_toggle_epoch_outside_the_grid_raises():
    ev = make(30, 10)
    with pytest.raises(IndexError):
        ev.toggle_epoch(3, 10)
    with pytest.raises(IndexError):
        ev.toggle_epoch(3, -1)


# ---- erase ------------------------------------------------------------------


def test_erase_clips_ranges_out_of_every_slot():
    ev = make()
    ev.add(0, [(0, 100)])
    ev.add(4, [(40, 70), (90, 120)])
    ev.erase([(50, 95)])
    assert ev.spans(0) == [[0, 50], [95, 100]]
    assert ev.spans(4) == [[40, 50], [95, 120]]


def test_erase_with_several_ranges_and_whole_event_removal():
    ev = make()
    ev.add(2, [(0, 10), (20, 30), (40, 60)])
    ev.erase([(5, 8), (15, 35)])
    assert ev.spans(2) == [[0, 5], [8, 10], [40, 60]]


def test_erase_ignores_empty_ranges_and_misses():
    ev = make()
    ev.add(2, [(10, 20)])
    ev.erase([(15, 15), (30, 40)])
    assert ev.spans(2) == [[10, 20]]


# ---- clear ------------------------------------------------------------------


def test_clear_empties_one_slot_only():
    ev = make()
    ev.add(1, [(10, 20)])
    ev.add(2, [(10, 20)])
    ev.clear(1)
    assert ev.spans(1) == []
    assert ev.spans(2) == [[10, 20]]


def test_clear_keeps_the_label():
    ev = make()
    ev.set_label(1, "Spindle")
    ev.clear(1)
    assert ev.label(1) == "Spindle"


# ---- relabel ----------------------------------------------------------------


def test_relabel_moves_only_the_smallest_containing_event():
    ev = make()
    ev.add(1, [(0, 100)])
    ev.add(2, [(40, 60)])
    ev.add(3, [(0, 200)])
    assert ev.relabel(50, 5) is True
    assert ev.spans(1) == [[0, 100]]
    assert ev.spans(2) == []
    assert ev.spans(3) == [[0, 200]]
    assert ev.spans(5) == [[40, 60]]


def test_relabel_merges_into_the_target_slot():
    ev = make()
    ev.add(1, [(40, 60)])
    ev.add(5, [(50, 80), (100, 110)])
    ev.relabel(45, 5)
    assert ev.spans(1) == []
    assert ev.spans(5) == [[40, 80], [100, 110]]


def test_relabel_into_the_same_slot_changes_nothing():
    ev = make()
    ev.add(1, [(40, 60)])
    assert ev.relabel(50, 1) is True
    assert ev.spans(1) == [[40, 60]]


def test_relabel_without_event_under_the_time_returns_false():
    ev = make()
    ev.add(1, [(40, 60)])
    assert ev.relabel(70, 5) is False
    assert ev.spans(1) == [[40, 60]]
    assert ev.spans(5) == []


def test_relabel_to_unknown_slot_raises():
    ev = make()
    ev.add(1, [(40, 60)])
    with pytest.raises(IndexError):
        ev.relabel(50, 13)


# ---- drop -------------------------------------------------------------------


def test_drop_removes_every_containing_event_in_every_slot():
    ev = make()
    ev.add(1, [(0, 100)])
    ev.add(2, [(40, 60)])
    ev.add(3, [(70, 80)])
    assert ev.drop(50) == 2
    assert ev.spans(1) == []
    assert ev.spans(2) == []
    assert ev.spans(3) == [[70, 80]]


def test_drop_removes_event_on_a_shared_border_in_all_slots_and_only_those():
    ev = make()
    ev.add(1, [(0, 10), (11, 20)])
    ev.add(1, [(30, 40)])
    ev.add(2, [(10, 25)])
    assert ev.drop(10) == 2
    assert ev.spans(1) == [[11, 20], [30, 40]]
    assert ev.spans(2) == []


def test_drop_without_event_under_the_time_returns_zero():
    ev = make()
    ev.add(1, [(40, 60)])
    assert ev.drop(10) == 0
    assert ev.spans(1) == [[40, 60]]


# ---- derived epochs ---------------------------------------------------------


def test_epochs_are_zero_based_per_event():
    ev = make(30, 10)
    ev.add(1, [(10, 40), (100, 130)])
    assert ev.epochs(1) == [[0, 1], [3, 4]]


def test_whole_epoch_event_refers_to_its_own_epoch_only():
    ev = make(30, 10)
    ev.add(1, [(0, 30)])
    ev.add(2, [(30, 60)])
    ev.add(3, [(60, 90), (120, 150)])
    assert ev.epochs(1) == [[0]]
    assert ev.epochs(2) == [[1]]
    assert ev.epochs(3) == [[2], [4]]


def test_event_ending_on_an_epoch_border_does_not_reach_the_next_epoch():
    ev = make(30, 10)
    ev.add(1, [(20, 60)])
    assert ev.epochs(1) == [[0, 1]]


def test_event_starting_on_an_epoch_border_does_not_reach_the_previous_epoch():
    ev = make(30, 10)
    ev.add(1, [(30, 45)])
    assert ev.epochs(1) == [[1]]


def test_event_inside_one_epoch_refers_to_it():
    ev = make(30, 10)
    ev.add(1, [(33, 37)])
    assert ev.epochs(1) == [[1]]


def test_epochs_are_clipped_to_the_epoch_count():
    ev = make(30, 3)
    ev.add(1, [(50, 200)])
    assert ev.epochs(1) == [[1, 2]]


def test_spans_past_the_recording_end_are_kept_with_no_epochs():
    ev = make(30, 3)
    ev.add(1, [(100, 200), (10, 20)])
    assert ev.spans(1) == [[10, 20], [100, 200]]
    assert ev.epochs(1) == [[0], []]
    assert ev.covered_epochs(1) == {0}


def test_shrinking_the_recording_keeps_spans_and_clips_epochs():
    ev = make(30, 10)
    ev.add(1, [(200, 280)])
    assert ev.epochs(1) == [[6, 7, 8, 9]]
    ev.set_grid(30, 7)
    assert ev.spans(1) == [[200, 280]]
    assert ev.epochs(1) == [[6]]
    ev.set_grid(30, 10)
    assert ev.epochs(1) == [[6, 7, 8, 9]]


def test_epochs_follow_a_new_epoch_length():
    ev = make(30, 10)
    ev.add(1, [(10, 70)])
    assert ev.epochs(1) == [[0, 1, 2]]
    ev.set_grid(20, 15)
    assert ev.spans(1) == [[10, 70]]
    assert ev.epochs(1) == [[0, 1, 2, 3]]
    ev.set_grid(60, 5)
    assert ev.epochs(1) == [[0, 1]]


def test_whole_epoch_rule_follows_the_new_epoch_length():
    ev = make(30, 10)
    ev.add(1, [(60, 90)])
    ev.set_grid(10, 30)
    assert ev.epochs(1) == [[6, 7, 8]]


def test_epochs_tolerate_float_noise_at_epoch_borders():
    ev = make(30, 10)
    ev.add(1, [(30 - 1e-9, 60 + 1e-9)])
    assert ev.epochs(1) == [[1]]


def test_toggled_epoch_has_exactly_that_epoch():
    ev = make(30, 10)
    ev.toggle_epoch(1, 4)
    assert ev.epochs(1) == [[4]]


def test_split_event_epochs_exclude_the_carved_epoch():
    ev = make(30, 10)
    ev.add(1, [(0, 150)])
    ev.toggle_epoch(1, 2)
    assert ev.epochs(1) == [[0, 1], [3, 4]]
    assert ev.covered_epochs(1) == {0, 1, 3, 4}


# ---- queries ----------------------------------------------------------------


def test_artefact_epochs_cover_slot_zero_only():
    ev = make(30, 10)
    ev.add(0, [(10, 40), (100, 130)])
    ev.add(1, [(200, 250)])
    assert ev.artefact_epochs() == {0, 1, 3, 4}
    assert ev.covered_epochs(1) == {6, 7, 8}


def test_artefact_epochs_empty_without_slot_zero_events():
    ev = make()
    ev.add(2, [(0, 100)])
    assert ev.artefact_epochs() == set()


def test_covered_epochs_union_over_overlapping_slots_stays_per_slot():
    ev = make(30, 10)
    ev.add(0, [(0, 60)])
    ev.add(1, [(30, 90)])
    assert ev.artefact_epochs() == {0, 1}
    assert ev.covered_epochs(1) == {1, 2}


def test_events_in_epoch_lists_slot_start_end_of_overlapping_events():
    ev = make(30, 10)
    ev.add(2, [(10, 40)])
    ev.add(5, [(30, 60), (100, 110)])
    ev.add(0, [(0, 30)])
    assert ev.events_in_epoch(1) == [(2, 10, 40), (5, 30, 60)]
    assert ev.events_in_epoch(0) == [(0, 0, 30), (2, 10, 40)]
    assert ev.events_in_epoch(7) == []


def test_next_event_epoch_searches_forward_then_wraps():
    ev = make(30, 10)
    ev.add(1, [(60, 90)])
    ev.add(4, [(180, 210)])
    assert ev.next_event_epoch(0) == 2
    assert ev.next_event_epoch(2) == 6
    assert ev.next_event_epoch(6) == 2
    assert ev.next_event_epoch(9) == 2


def test_next_event_epoch_single_event_found_from_everywhere_including_itself():
    ev = make(30, 10)
    ev.add(1, [(60, 90)])
    assert ev.next_event_epoch(2) == 2
    assert ev.next_event_epoch(5) == 2


def test_next_event_epoch_none_without_events_or_epochs():
    ev = make(30, 10)
    assert ev.next_event_epoch(3) is None
    ev.add(1, [(500, 600)])  # past the recording end: no epochs
    assert ev.next_event_epoch(3) is None


def test_count_and_total_duration_per_slot():
    ev = make()
    ev.add(1, [(10, 20), (30, 45)])
    ev.add(2, [(0, 5)])
    assert (ev.count(1), ev.total_duration(1)) == (2, 25)
    assert (ev.count(2), ev.total_duration(2)) == (1, 5)
    assert (ev.count(3), ev.total_duration(3)) == (0, 0)


def test_count_and_duration_include_spans_past_the_recording_end():
    ev = make(30, 3)
    ev.add(1, [(100, 160)])
    assert (ev.count(1), ev.total_duration(1)) == (1, 60)
