# Worked examples

Section 12 of the specification gives worked examples, each with its inputs and its required outcome. Every example has an executable form in the conformance suite. This page lists the fixtures keyed to each example, so you can read the JSON next to the prose.

To run the fixtures for one example, pass any fragment of their names. For example:

```bash
bash scripts/run_conformance.sh section_1_5
```

§1.5, "A story, end to end", is the best place to start. Its fixtures are `T13_01_section_1_5_walkthrough_day_by_day` (the record day by day) and `T18_18_what_remains_on_the_section_1_5_example_at_each_rows_cutoff` ("what remains" at the end of each day).

## 12.1 Identity (2.3, 4.5)

- [`T01_01_identity_worked_example`](../conformance/fixtures/T01_01_identity_worked_example.json)
- [`T10_05_equal_instants_keep_distinct_contexts_and_after_orders_them`](../conformance/fixtures/T10_05_equal_instants_keep_distinct_contexts_and_after_orders_them.json)
- [`T16_12_unrelated_scopes_never_compare`](../conformance/fixtures/T16_12_unrelated_scopes_never_compare.json)
- [`T16_13_renumbering_keeps_identity`](../conformance/fixtures/T16_13_renumbering_keeps_identity.json)

## 12.2 Sparse carry-forward (5.2)

- [`T02_01_sparse_carry_forward_worked_example`](../conformance/fixtures/T02_01_sparse_carry_forward_worked_example.json)
- [`T08_13_source_is_the_communication_not_the_party`](../conformance/fixtures/T08_13_source_is_the_communication_not_the_party.json)

## 12.3 Structured replacement (5.4)

- [`T03_01_structured_replacement_worked_example`](../conformance/fixtures/T03_01_structured_replacement_worked_example.json)
- [`T03_04_lists_replace_as_whole`](../conformance/fixtures/T03_04_lists_replace_as_whole.json)

## 12.4 Comparison (5.3, 5.5)

- [`T04_01_empty_equivalence_null_and_blank`](../conformance/fixtures/T04_01_empty_equivalence_null_and_blank.json)
- [`T04_03_null_versus_omission`](../conformance/fixtures/T04_03_null_versus_omission.json)
- [`T04_04_ordinary_values_are_not_empty`](../conformance/fixtures/T04_04_ordinary_values_are_not_empty.json)
- [`T04_07_numeric_equality_and_precision`](../conformance/fixtures/T04_07_numeric_equality_and_precision.json)
- [`T04_09_declared_interpretation_fire_rating`](../conformance/fixtures/T04_09_declared_interpretation_fire_rating.json)
- [`T04_11_required_null_met_by_explicit_null`](../conformance/fixtures/T04_11_required_null_met_by_explicit_null.json)
- [`T09_04_empty_answers_and_required_null`](../conformance/fixtures/T09_04_empty_answers_and_required_null.json)

## 12.5 Withdrawal of a value (6.5, 6.7.4)

- [`T05_01_withdrawn_latest_value_has_no_current_value`](../conformance/fixtures/T05_01_withdrawn_latest_value_has_no_current_value.json)
- [`T05_02_reassertion_after_withdrawal_reads_new_value`](../conformance/fixtures/T05_02_reassertion_after_withdrawal_reads_new_value.json)
- [`T05_03_withdrawn_differs_from_explicit_null_and_never_asserted`](../conformance/fixtures/T05_03_withdrawn_differs_from_explicit_null_and_never_asserted.json)
- [`T05_09_unfulfilled_request_is_outstanding_after_source_withdraws_value`](../conformance/fixtures/T05_09_unfulfilled_request_is_outstanding_after_source_withdraws_value.json)
- [`T05_10_withdrawn_value_leaves_request_not_yet_due_before_scope`](../conformance/fixtures/T05_10_withdrawn_value_leaves_request_not_yet_due_before_scope.json)
- [`T05_11_fulfilled_request_stays_fulfilled_after_evidence_is_withdrawn`](../conformance/fixtures/T05_11_fulfilled_request_stays_fulfilled_after_evidence_is_withdrawn.json)
- [`T05_12_superseded_value_is_not_revived_as_evidence_reassertion_fulfills`](../conformance/fixtures/T05_12_superseded_value_is_not_revived_as_evidence_reassertion_fulfills.json)

## 12.6 Partial and bulk withdrawal (6.3, 6.7.2, 6.7.3)

- [`T06_01_property_withdrawal_leaves_other_property_open_and_mixed_result`](../conformance/fixtures/T06_01_property_withdrawal_leaves_other_property_open_and_mixed_result.json)
- [`T06_02_withdrawing_one_support_leaves_expectation_in_force`](../conformance/fixtures/T06_02_withdrawing_one_support_leaves_expectation_in_force.json)
- [`T06_03_withdrawing_one_supports_coverage_of_one_property`](../conformance/fixtures/T06_03_withdrawing_one_supports_coverage_of_one_property.json)
- [`T06_04_expectation_property_withdrawal_ends_it_for_every_support`](../conformance/fixtures/T06_04_expectation_property_withdrawal_ends_it_for_every_support.json)
- [`T06_05_every_support_withdrawn_reads_withdrawn_not_not_in_force`](../conformance/fixtures/T06_05_every_support_withdrawn_reads_withdrawn_not_not_in_force.json)
- [`T06_06_fulfilled_property_survives_support_withdrawal_and_reaffirmation`](../conformance/fixtures/T06_06_fulfilled_property_survives_support_withdrawal_and_reaffirmation.json)
- [`T06_07_withdrawal_effective_later_ends_supports_covering_at_effective_time`](../conformance/fixtures/T06_07_withdrawal_effective_later_ends_supports_covering_at_effective_time.json)
- [`T06_08_withdrawal_ends_earlier_support_with_later_effective_time`](../conformance/fixtures/T06_08_withdrawal_ends_earlier_support_with_later_effective_time.json)
- [`T06_09_support_after_withdrawal_begins_new_period_and_resets_freshness`](../conformance/fixtures/T06_09_support_after_withdrawal_begins_new_period_and_resets_freshness.json)
- [`T06_10_bulk_withdrawal_of_statements_on_two_items_with_fixed_targets`](../conformance/fixtures/T06_10_bulk_withdrawal_of_statements_on_two_items_with_fixed_targets.json)
- [`T06_11_bulk_withdrawal_of_expectations_on_two_items`](../conformance/fixtures/T06_11_bulk_withdrawal_of_expectations_on_two_items.json)
- [`T06_17_withdrawn_names_the_withdrawals_of_the_last_in_force_period`](../conformance/fixtures/T06_17_withdrawn_names_the_withdrawals_of_the_last_in_force_period.json)

## 12.7 Expectation identity and conflict (6.1, 6.3, 7.1.5)

- [`T07_01_expectation_and_statement_coexist_on_same_subject_and_source`](../conformance/fixtures/T07_01_expectation_and_statement_coexist_on_same_subject_and_source.json)
- [`T07_02_reaffirmation_references_the_same_expectation`](../conformance/fixtures/T07_02_reaffirmation_references_the_same_expectation.json)
- [`T07_05_competing_expectations_conflict_whatever_their_milestones`](../conformance/fixtures/T07_05_competing_expectations_conflict_whatever_their_milestones.json)
- [`T07_06_reversed_recording_order_changes_nothing`](../conformance/fixtures/T07_06_reversed_recording_order_changes_nothing.json)
- [`T07_07_fulfilling_one_expectation_ends_the_conflict_story`](../conformance/fixtures/T07_07_fulfilling_one_expectation_ends_the_conflict_story.json)
- [`T07_08_withdrawing_the_paint_expectation_ends_the_conflict`](../conformance/fixtures/T07_08_withdrawing_the_paint_expectation_ends_the_conflict.json)
- [`T07_09_withdrawing_the_stain_expectation_ends_the_conflict_at_effective_time`](../conformance/fixtures/T07_09_withdrawing_the_stain_expectation_ends_the_conflict_at_effective_time.json)
- [`T07_10_review_of_expectation_conflict_changes_no_standing`](../conformance/fixtures/T07_10_review_of_expectation_conflict_changes_no_standing.json)
- [`T07_11_ignoring_expectation_conflict_changes_no_standing`](../conformance/fixtures/T07_11_ignoring_expectation_conflict_changes_no_standing.json)
- [`T07_12_two_obligated_sources_are_two_expectations`](../conformance/fixtures/T07_12_two_obligated_sources_are_two_expectations.json)
- [`T11_07_expectations_conflict_by_the_same_comparison`](../conformance/fixtures/T11_07_expectations_conflict_by_the_same_comparison.json)
- [`T13_26_expectation_conflict_story_ends_by_fulfillment`](../conformance/fixtures/T13_26_expectation_conflict_story_ends_by_fulfillment.json)
- [`T13_27_expectation_conflict_story_ends_when_side_withdrawn`](../conformance/fixtures/T13_27_expectation_conflict_story_ends_when_side_withdrawn.json)

## 12.8 Source qualification (3.1, 3.3)

- [`T08_01_named_communication_requirement`](../conformance/fixtures/T08_01_named_communication_requirement.json)
- [`T08_02_party_requirement_met_by_any_qualifying_communication`](../conformance/fixtures/T08_02_party_requirement_met_by_any_qualifying_communication.json)
- [`T08_03_agent_criterion_matched_by_identity_only`](../conformance/fixtures/T08_03_agent_criterion_matched_by_identity_only.json)
- [`T08_08_disagreeing_criteria_make_qualification_ambiguous`](../conformance/fixtures/T08_08_disagreeing_criteria_make_qualification_ambiguous.json)
- [`T08_10_qualifying_email_does_not_outrank_the_schedule`](../conformance/fixtures/T08_10_qualifying_email_does_not_outrank_the_schedule.json)
- [`T08_13_source_is_the_communication_not_the_party`](../conformance/fixtures/T08_13_source_is_the_communication_not_the_party.json)
- [`T08_14_by_party_and_by_source_reads`](../conformance/fixtures/T08_14_by_party_and_by_source_reads.json)

## 12.9 Fulfillment (6.2, 6.5)

- [`T09_01_existing_evidence_fulfills_at_establishment_unless_fresh`](../conformance/fixtures/T09_01_existing_evidence_fulfills_at_establishment_unless_fresh.json)
- [`T09_02_monday_evidence_imported_thursday_gives_same_tuesday_fulfillment`](../conformance/fixtures/T09_02_monday_evidence_imported_thursday_gives_same_tuesday_fulfillment.json)
- [`T09_03_suggested_value_answered_differently_fulfills_required_does_not`](../conformance/fixtures/T09_03_suggested_value_answered_differently_fulfills_required_does_not.json)
- [`T09_04_empty_answers_and_required_null`](../conformance/fixtures/T09_04_empty_answers_and_required_null.json)
- [`T09_06_date_only_issue_on_establishment_day_is_ambiguous_for_fresh`](../conformance/fixtures/T09_06_date_only_issue_on_establishment_day_is_ambiguous_for_fresh.json)
- [`T09_07_at_milestone_evidence_is_fixed_by_target_despite_later_revision`](../conformance/fixtures/T09_07_at_milestone_evidence_is_fixed_by_target_despite_later_revision.json)
- [`T09_08_at_milestone_evidence_withdrawn_before_establishment_does_not_fulfill`](../conformance/fixtures/T09_08_at_milestone_evidence_withdrawn_before_establishment_does_not_fulfill.json)
- [`T09_09_skipped_preferred_issuance_does_not_block_fulfillment`](../conformance/fixtures/T09_09_skipped_preferred_issuance_does_not_block_fulfillment.json)
- [`T09_10_friday_submission_against_wednesday_deadline_is_late_by_two_days`](../conformance/fixtures/T09_10_friday_submission_against_wednesday_deadline_is_late_by_two_days.json)
- [`T09_11_evidence_at_exact_deadline_is_on_time_later_minutes_are_late`](../conformance/fixtures/T09_11_evidence_at_exact_deadline_is_on_time_later_minutes_are_late.json)
- [`T09_12_date_only_issue_on_deadline_day_fulfills_with_ambiguous_timeliness`](../conformance/fixtures/T09_12_date_only_issue_on_deadline_day_fulfills_with_ambiguous_timeliness.json)
- [`T09_13_by_is_outstanding_not_overdue_before_deadline_any_is_never_overdue`](../conformance/fixtures/T09_13_by_is_outstanding_not_overdue_before_deadline_any_is_never_overdue.json)
- [`T09_14_at_milestone_requirement_not_yet_due_until_published`](../conformance/fixtures/T09_14_at_milestone_requirement_not_yet_due_until_published.json)
- [`T09_15_later_contrary_value_leaves_fulfillment_intact`](../conformance/fixtures/T09_15_later_contrary_value_leaves_fulfillment_intact.json)
- [`T09_25_intervals_that_meet_are_ordered`](../conformance/fixtures/T09_25_intervals_that_meet_are_ordered.json)
- [`T09_30_accept_empty_interpretation_lets_null_answer_a_request`](../conformance/fixtures/T09_30_accept_empty_interpretation_lets_null_answer_a_request.json)

## 12.10 Time and distribution (4.2, 4.3, 4.4)

- [`T10_01_cross_schedule_milestones_ordered_by_publication_instant`](../conformance/fixtures/T10_01_cross_schedule_milestones_ordered_by_publication_instant.json)
- [`T10_02_event_and_milestone_share_one_chronology`](../conformance/fixtures/T10_02_event_and_milestone_share_one_chronology.json)
- [`T10_03_date_and_minute_instants_same_day_are_unordered`](../conformance/fixtures/T10_03_date_and_minute_instants_same_day_are_unordered.json)
- [`T10_06_same_schedule_milestones_ordered_by_ordinal`](../conformance/fixtures/T10_06_same_schedule_milestones_ordered_by_ordinal.json)
- [`T10_09_competing_publication_instants_are_ambiguous`](../conformance/fixtures/T10_09_competing_publication_instants_are_ambiguous.json)
- [`T10_11_publication_and_later_distribution_history`](../conformance/fixtures/T10_11_publication_and_later_distribution_history.json)
- [`T10_12_issuance_distribution_limited_to_that_issuance`](../conformance/fixtures/T10_12_issuance_distribution_limited_to_that_issuance.json)
- [`T10_14_participant_view_of_a_withdrawal_recorded_from_later_minutes`](../conformance/fixtures/T10_14_participant_view_of_a_withdrawal_recorded_from_later_minutes.json)
- [`T10_15_later_distributed_withdrawal_applies_at_its_effective_time`](../conformance/fixtures/T10_15_later_distributed_withdrawal_applies_at_its_effective_time.json)
- [`T10_20_intervals_that_meet_are_ordered_against_cutoffs`](../conformance/fixtures/T10_20_intervals_that_meet_are_ordered_against_cutoffs.json)

## 12.11 Comparison paths (7.1)

- [`T11_01_wednesday_conflict_uses_each_sides_applicable_evidence`](../conformance/fixtures/T11_01_wednesday_conflict_uses_each_sides_applicable_evidence.json)
- [`T11_02_thursday_issue_answers_change_and_conflict_separately`](../conformance/fixtures/T11_02_thursday_issue_answers_change_and_conflict_separately.json)
- [`T11_03_each_property_keeps_its_own_origin`](../conformance/fixtures/T11_03_each_property_keeps_its_own_origin.json)
- [`T11_06_due_work_is_visible_without_submissions`](../conformance/fixtures/T11_06_due_work_is_visible_without_submissions.json)

## 12.12 Review and attention (7.4, 9.5)

- [`T08_14_by_party_and_by_source_reads`](../conformance/fixtures/T08_14_by_party_and_by_source_reads.json)
- [`T12_01_no_change_review_keeps_conflict_open_and_disagreeing`](../conformance/fixtures/T12_01_no_change_review_keeps_conflict_open_and_disagreeing.json)
- [`T12_02_review_leaves_independent_expectation_standing`](../conformance/fixtures/T12_02_review_leaves_independent_expectation_standing.json)
- [`T12_03_ignored_story_counts_until_attention_filter_requested`](../conformance/fixtures/T12_03_ignored_story_counts_until_attention_filter_requested.json)
- [`T12_05_by_party_returns_statements_and_acts_of_party`](../conformance/fixtures/T12_05_by_party_returns_statements_and_acts_of_party.json)
- [`T12_06_reader_interpretation_reports_match_without_changing_story`](../conformance/fixtures/T12_06_reader_interpretation_reports_match_without_changing_story.json)
- [`T12_07_change_required_review_supports_but_does_not_end_conflict`](../conformance/fixtures/T12_07_change_required_review_supports_but_does_not_end_conflict.json)

## 12.13 Story chronology (7.2, 7.3)

- [`T13_01_section_1_5_walkthrough_day_by_day`](../conformance/fixtures/T13_01_section_1_5_walkthrough_day_by_day.json)
- [`T13_02_identical_replay_and_comparison_reads_open_no_story`](../conformance/fixtures/T13_02_identical_replay_and_comparison_reads_open_no_story.json)
- [`T13_03_unreviewed_evidence_change_adds_dated_detection`](../conformance/fixtures/T13_03_unreviewed_evidence_change_adds_dated_detection.json)
- [`T13_04_change_after_review_opens_related_story`](../conformance/fixtures/T13_04_change_after_review_opens_related_story.json)
- [`T13_05_backfilled_agreement_splits_story`](../conformance/fixtures/T13_05_backfilled_agreement_splits_story.json)
- [`T13_06_backfilled_issuance_joins_unreviewed_stories`](../conformance/fixtures/T13_06_backfilled_issuance_joins_unreviewed_stories.json)
- [`T13_07_join_case_in_event_order_gives_same_account`](../conformance/fixtures/T13_07_join_case_in_event_order_gives_same_account.json)
- [`T13_08_backfill_after_review_opens_related_story_at_review_time`](../conformance/fixtures/T13_08_backfill_after_review_opens_related_story_at_review_time.json)
- [`T13_09_withdrawal_of_side_ends_story_and_return_opens_related`](../conformance/fixtures/T13_09_withdrawal_of_side_ends_story_and_return_opens_related.json)
- [`T13_10_alignment_ends_story_and_return_opens_related`](../conformance/fixtures/T13_10_alignment_ends_story_and_return_opens_related.json)
- [`T13_12_change_story_approval_ends_it_and_withdrawal_reopens`](../conformance/fixtures/T13_12_change_story_approval_ends_it_and_withdrawal_reopens.json)
- [`T13_13_backfill_inside_reviewed_change_is_reconstructed`](../conformance/fixtures/T13_13_backfill_inside_reviewed_change_is_reconstructed.json)
- [`T13_14_correction_shows_sides_never_disagreed`](../conformance/fixtures/T13_14_correction_shows_sides_never_disagreed.json)
- [`T13_15_correction_aligns_later_assertion_ends_by_alignment`](../conformance/fixtures/T13_15_correction_aligns_later_assertion_ends_by_alignment.json)
- [`T13_16_correction_leaving_sides_unequal_keeps_story_open`](../conformance/fixtures/T13_16_correction_leaving_sides_unequal_keeps_story_open.json)
- [`T13_17_erroneous_continuation_basis_keeps_story_open`](../conformance/fixtures/T13_17_erroneous_continuation_basis_keeps_story_open.json)
- [`T13_19_corrected_ending_of_reviewed_story_records_boundary`](../conformance/fixtures/T13_19_corrected_ending_of_reviewed_story_records_boundary.json)
- [`T13_20_corrected_ending_of_unreviewed_story_joins_stories`](../conformance/fixtures/T13_20_corrected_ending_of_unreviewed_story_joins_stories.json)
- [`T13_21_withdrawn_review_then_change_continues_latest_story`](../conformance/fixtures/T13_21_withdrawn_review_then_change_continues_latest_story.json)
- [`T13_22_a_normalization_ends_a_story_from_its_effective_time`](../conformance/fixtures/T13_22_a_normalization_ends_a_story_from_its_effective_time.json)
- [`T13_23_tied_revision_after_review_by_after_opens_related_story`](../conformance/fixtures/T13_23_tied_revision_after_review_by_after_opens_related_story.json)
- [`T13_24_tied_review_after_revision_by_after_covers_revision`](../conformance/fixtures/T13_24_tied_review_after_revision_by_after_covers_revision.json)
- [`T13_25_tied_revision_without_after_treated_as_after_review`](../conformance/fixtures/T13_25_tied_revision_without_after_treated_as_after_review.json)
- [`T13_29_family_counted_once_superseded_story_keeps_its_standing`](../conformance/fixtures/T13_29_family_counted_once_superseded_story_keeps_its_standing.json)
- [`T13_33_stories_whose_sides_never_disagreed_have_an_empty_interval`](../conformance/fixtures/T13_33_stories_whose_sides_never_disagreed_have_an_empty_interval.json)
- [`T13_34_correction_leaving_a_side_without_value_ends_the_story_by_correction`](../conformance/fixtures/T13_34_correction_leaving_a_side_without_value_ends_the_story_by_correction.json)
- [`T13_36_generated_split_records_and_related_stories_both_ways`](../conformance/fixtures/T13_36_generated_split_records_and_related_stories_both_ways.json)
- [`T13_37_join_reconciliation_content_and_continuation_on_the_representative`](../conformance/fixtures/T13_37_join_reconciliation_content_and_continuation_on_the_representative.json)

## 12.14 Recorded basis (7.5)

- [`T14_01_review_basis_kept_after_backfilled_agreement`](../conformance/fixtures/T14_01_review_basis_kept_after_backfilled_agreement.json)
- [`T14_02_participant_not_assumed_to_have_undistributed_evidence`](../conformance/fixtures/T14_02_participant_not_assumed_to_have_undistributed_evidence.json)
- [`T14_03_instruction_reconstructable_from_minutes`](../conformance/fixtures/T14_03_instruction_reconstructable_from_minutes.json)
- [`T14_06_backfilled_alignment_before_review_records_a_boundary_and_opens_no_story`](../conformance/fixtures/T14_06_backfilled_alignment_before_review_records_a_boundary_and_opens_no_story.json)

## 12.15 Error operations (8.1, 8.3, 8.5)

- [`T15_01_identical_reimport_is_noop`](../conformance/fixtures/T15_01_identical_reimport_is_noop.json)
- [`T15_02_changed_content_at_occupied_triple_rejected`](../conformance/fixtures/T15_02_changed_content_at_occupied_triple_rejected.json)
- [`T15_03_genuine_revision_is_new_assertion_at_new_context`](../conformance/fixtures/T15_03_genuine_revision_is_new_assertion_at_new_context.json)
- [`T15_04_replace_correction_restores_dropped_member_at_every_cutoff`](../conformance/fixtures/T15_04_replace_correction_restores_dropped_member_at_every_cutoff.json)
- [`T15_08_relocated_instruction_limits_standing_until_support_corrected`](../conformance/fixtures/T15_08_relocated_instruction_limits_standing_until_support_corrected.json)
- [`T15_10_duplicate_without_dependents_removed_and_triple_freed`](../conformance/fixtures/T15_10_duplicate_without_dependents_removed_and_triple_freed.json)
- [`T15_11_wrong_value_removed_and_true_value_rewritten`](../conformance/fixtures/T15_11_wrong_value_removed_and_true_value_rewritten.json)
- [`T15_12_entry_cited_by_review_refused_then_corrected`](../conformance/fixtures/T15_12_entry_cited_by_review_refused_then_corrected.json)
- [`T15_13_fulfilling_evidence_refused_then_corrected`](../conformance/fixtures/T15_13_fulfilling_evidence_refused_then_corrected.json)
- [`T15_14_sole_support_of_fulfilled_expectation_refused`](../conformance/fixtures/T15_14_sole_support_of_fulfilled_expectation_refused.json)
- [`T15_15_publication_with_assertions_at_milestone_refused`](../conformance/fixtures/T15_15_publication_with_assertions_at_milestone_refused.json)
- [`T15_16_withdrawal_ending_a_story_refused`](../conformance/fixtures/T15_16_withdrawal_ending_a_story_refused.json)
- [`T15_17_confirm_after_intervening_change_is_stale`](../conformance/fixtures/T15_17_confirm_after_intervening_change_is_stale.json)
- [`T15_26_relocation_limitations_name_correction_and_record`](../conformance/fixtures/T15_26_relocation_limitations_name_correction_and_record.json)
- [`T18_22_relocated_expectation_is_a_limitation_entry_until_its_support_is_corrected`](../conformance/fixtures/T18_22_relocated_expectation_is_a_limitation_entry_until_its_support_is_corrected.json)

## 12.16 Structural history (8.6, 8.7)

- [`T16_01_disconnect_and_reconnect_one_connection`](../conformance/fixtures/T16_01_disconnect_and_reconnect_one_connection.json)
- [`T16_02_second_cycle_history_reconstructed_from_acts`](../conformance/fixtures/T16_02_second_cycle_history_reconstructed_from_acts.json)
- [`T16_03_erroneous_disconnect_correction_rederives_state`](../conformance/fixtures/T16_03_erroneous_disconnect_correction_rederives_state.json)
- [`T16_08_scope_follows_connections_forward`](../conformance/fixtures/T16_08_scope_follows_connections_forward.json)
- [`T16_10_disconnection_leaves_later_scope_and_ends_no_expectation`](../conformance/fixtures/T16_10_disconnection_leaves_later_scope_and_ends_no_expectation.json)
- [`T16_12_unrelated_scopes_never_compare`](../conformance/fixtures/T16_12_unrelated_scopes_never_compare.json)
- [`T16_14_retirement_omission_and_disconnection_withdraw_nothing`](../conformance/fixtures/T16_14_retirement_omission_and_disconnection_withdraw_nothing.json)
- [`T16_16_scope_item_is_a_member_of_its_own_scope`](../conformance/fixtures/T16_16_scope_item_is_a_member_of_its_own_scope.json)
- [`T16_17_exact_read_of_a_connection_returns_materialized_and_derived_state`](../conformance/fixtures/T16_17_exact_read_of_a_connection_returns_materialized_and_derived_state.json)

## 12.17 Portability and extensions (5.1, 10.4)

- [`T17_04_unknown_action_counts_as_nothing`](../conformance/fixtures/T17_04_unknown_action_counts_as_nothing.json)
- [`T17_09_reads_report_extension_records_as_unsupported`](../conformance/fixtures/T17_09_reads_report_extension_records_as_unsupported.json)
- [`T17_10_declared_reference_extension_refuses_removal`](../conformance/fixtures/T17_10_declared_reference_extension_refuses_removal.json)
- [`T17_12_declared_reference_extension_refuses_item_removal_while_any_record_carries_it`](../conformance/fixtures/T17_12_declared_reference_extension_refuses_item_removal_while_any_record_carries_it.json)
- [`T18_63_a_normalization_naming_an_interpretation_the_reference_lacks_is_refused`](../conformance/fixtures/T18_63_a_normalization_naming_an_interpretation_the_reference_lacks_is_refused.json)

## 12.18 The reference package

This example describes the package itself and has no fixture of its own: the whole suite is its executable form.

## 12.19 Recorded beginnings and endings (7.6, 7.7, 9.5.7, 9.5.8)

- [`T18_01_conflict_story_begin_and_end_acts`](../conformance/fixtures/T18_01_conflict_story_begin_and_end_acts.json)
- [`T18_02_change_story_begin_and_end_acts`](../conformance/fixtures/T18_02_change_story_begin_and_end_acts.json)
- [`T18_03_expectation_property_begin_and_end_acts`](../conformance/fixtures/T18_03_expectation_property_begin_and_end_acts.json)
- [`T18_05_conflict_story_ends_by_withdrawal_and_by_fulfillment_of_an_expectation_side`](../conformance/fixtures/T18_05_conflict_story_ends_by_withdrawal_and_by_fulfillment_of_an_expectation_side.json)
- [`T18_07_split_revises_the_ending_and_records_the_successors_transitions`](../conformance/fixtures/T18_07_split_revises_the_ending_and_records_the_successors_transitions.json)
- [`T18_08_join_revises_the_apparent_ending_and_the_continued_story_to_null`](../conformance/fixtures/T18_08_join_revises_the_apparent_ending_and_the_continued_story_to_null.json)
- [`T18_10_correction_showing_no_disagreement_revises_the_begin_act_to_null`](../conformance/fixtures/T18_10_correction_showing_no_disagreement_revises_the_begin_act_to_null.json)
- [`T18_12_withdrawn_approval_reopens_a_change_story_with_a_new_period`](../conformance/fixtures/T18_12_withdrawn_approval_reopens_a_change_story_with_a_new_period.json)
- [`T18_13_new_period_after_withdrawal_terminal_fulfillment_and_an_ending_revised_ahead_of_its_time`](../conformance/fixtures/T18_13_new_period_after_withdrawal_terminal_fulfillment_and_an_ending_revised_ahead_of_its_time.json)
- [`T18_14_withdrawal_with_a_later_effective_time_records_its_end_now`](../conformance/fixtures/T18_14_withdrawal_with_a_later_effective_time_records_its_end_now.json)
- [`T18_18_what_remains_on_the_section_1_5_example_at_each_rows_cutoff`](../conformance/fixtures/T18_18_what_remains_on_the_section_1_5_example_at_each_rows_cutoff.json)
- [`T18_19_what_remains_nesting_parents_children_and_succession`](../conformance/fixtures/T18_19_what_remains_nesting_parents_children_and_succession.json)
- [`T18_25_fixture_policy_keeps_a_directed_change_open_until_its_expectation_is_fulfilled`](../conformance/fixtures/T18_25_fixture_policy_keeps_a_directed_change_open_until_its_expectation_is_fulfilled.json)
- [`T18_29_unimplemented_policy_ends_a_conflict_story_that_still_disagrees`](../conformance/fixtures/T18_29_unimplemented_policy_ends_a_conflict_story_that_still_disagrees.json)
- [`T18_32_explicit_baseline_begin_and_end_acts_are_validated_against_the_derivation`](../conformance/fixtures/T18_32_explicit_baseline_begin_and_end_acts_are_validated_against_the_derivation.json)
- [`T18_50_a_requirement_begun_by_the_review_of_one_story_has_its_records_on_that_story`](../conformance/fixtures/T18_50_a_requirement_begun_by_the_review_of_one_story_has_its_records_on_that_story.json)
- [`T18_51_adopt_policy_takes_effect_when_made_and_earlier_endings_stand`](../conformance/fixtures/T18_51_adopt_policy_takes_effect_when_made_and_earlier_endings_stand.json)
- [`T18_52_evidence_at_an_unpublished_milestone_records_no_ending_until_the_milestone_is_published`](../conformance/fixtures/T18_52_evidence_at_an_unpublished_milestone_records_no_ending_until_the_milestone_is_published.json)
- [`T18_53_a_beginning_tied_with_a_review_cites_the_disagreeing_document`](../conformance/fixtures/T18_53_a_beginning_tied_with_a_review_cites_the_disagreeing_document.json)
- [`T18_54_a_transition_caused_by_several_records_at_one_instant_cites_every_one`](../conformance/fixtures/T18_54_a_transition_caused_by_several_records_at_one_instant_cites_every_one.json)
- [`T18_65_a_story_with_no_period_through_a_normalization_reads_not_started_before_its_since`](../conformance/fixtures/T18_65_a_story_with_no_period_through_a_normalization_reads_not_started_before_its_since.json)

## 12.20 Normalization (7.3.8, 5.5.4, 6.5.1)

- [`T18_11_a_normalization_revises_recorded_transitions`](../conformance/fixtures/T18_11_a_normalization_revises_recorded_transitions.json)
- [`T18_43_a_normalization_ends_the_open_stories_whose_sides_it_matches_at_its_effective_time`](../conformance/fixtures/T18_43_a_normalization_ends_the_open_stories_whose_sides_it_matches_at_its_effective_time.json)
- [`T18_44_after_a_normalization_values_equal_under_it_are_neither_a_conflict_nor_a_change`](../conformance/fixtures/T18_44_after_a_normalization_values_equal_under_it_are_neither_a_conflict_nor_a_change.json)
- [`T18_46_evidence_that_meets_a_requirement_only_under_a_normalization_fulfils_it_from_then`](../conformance/fixtures/T18_46_evidence_that_meets_a_requirement_only_under_a_normalization_fulfils_it_from_then.json)
- [`T18_47_a_later_normalization_supersedes_an_earlier_one_from_its_own_effective_time`](../conformance/fixtures/T18_47_a_later_normalization_supersedes_an_earlier_one_from_its_own_effective_time.json)
- [`T18_60_a_requirement_keeps_its_own_interpretation_under_a_project_normalization`](../conformance/fixtures/T18_60_a_requirement_keeps_its_own_interpretation_under_a_project_normalization.json)
- [`T18_61_two_expectations_are_compared_under_their_own_interpretations`](../conformance/fixtures/T18_61_two_expectations_are_compared_under_their_own_interpretations.json)
- [`T18_62_a_reversal_of_the_interpretation_in_force_reopens_review_as_a_related_change_story`](../conformance/fixtures/T18_62_a_reversal_of_the_interpretation_in_force_reopens_review_as_a_related_change_story.json)
- [`T18_64_a_frame_requesting_literal_comparison_computes_literally_after_a_normalization`](../conformance/fixtures/T18_64_a_frame_requesting_literal_comparison_computes_literally_after_a_normalization.json)
- [`T18_65_a_story_with_no_period_through_a_normalization_reads_not_started_before_its_since`](../conformance/fixtures/T18_65_a_story_with_no_period_through_a_normalization_reads_not_started_before_its_since.json)
- [`T18_66_a_review_withdrawn_while_the_revision_changes_nothing_leaves_a_period_of_no_length`](../conformance/fixtures/T18_66_a_review_withdrawn_while_the_revision_changes_nothing_leaves_a_period_of_no_length.json)
