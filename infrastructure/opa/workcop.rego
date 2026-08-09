package safelytold.authz

default decision := {"allow": false, "reason": "default_deny"}

implicated if input.subject.id in input.resource.implicated_subject_ids
assigned if input.resource.id in input.subject.assigned_case_ids
valid_purpose if input.purpose != ""

identity_dual_control if {
  not input.request.identity_access
} else if {
  input.request.identity_access
  input.request.approval_count >= 2
  input.request.requester_id != input.request.approver_ids[_]
}

decision := {"allow": false, "reason": "recusal_required", "obligations": ["audit", "notify_ethics_admin"]} if implicated

decision := {"allow": false, "reason": "purpose_required"} if not valid_purpose

decision := {"allow": false, "reason": "assignment_required"} if {
  startswith(input.action, "case:")
  not assigned
}

decision := {"allow": false, "reason": "dual_control_required"} if not identity_dual_control

decision := {"allow": true, "reason": "conditions_satisfied", "obligations": ["audit", "bind_purpose", "mask_unneeded_fields"]} if {
  not implicated
  valid_purpose
  identity_dual_control
  not startswith(input.action, "case:")
} else := {"allow": true, "reason": "conditions_satisfied", "obligations": ["audit", "bind_purpose", "mask_unneeded_fields"]} if {
  not implicated
  valid_purpose
  identity_dual_control
  startswith(input.action, "case:")
  assigned
}
