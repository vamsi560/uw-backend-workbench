# Underwriter Management API Documentation

## Overview
The underwriter management system allows reassigning work items between underwriters of different experience levels (Junior, Senior, Principal, Manager).

## API Endpoints

### 1. List All Underwriters
**GET** `/api/underwriters`

Returns all active underwriters with their current details.

**Response Example:**
```json
{
  "underwriters": [
    {
      "id": 1,
      "name": "Sarah Johnson",
      "email": "sarah.johnson@company.com",
      "level": "SENIOR",
      "department": "Cyber Insurance",
      "specializations": ["cyber", "technology", "professional_liability"],
      "max_coverage_limit": 10000000.0,
      "workload": 5
    },
    {
      "id": 2,
      "name": "Emma Wilson",
      "email": "emma.wilson@company.com",
      "level": "JUNIOR",
      "department": "Cyber Insurance",
      "specializations": ["cyber", "small_business"],
      "max_coverage_limit": 2000000.0,
      "workload": 2
    }
  ]
}
```

### 2. List Underwriters by Experience Level
**GET** `/api/underwriters/by-level`

Groups underwriters by their experience level for easy UI dropdown population.

**Response Example:**
```json
{
  "underwriters_by_level": {
    "JUNIOR": [
      {
        "id": 3,
        "name": "Emma Wilson",
        "email": "emma.wilson@company.com",
        "department": "Cyber Insurance",
        "specializations": ["cyber", "small_business"],
        "max_coverage_limit": 2000000.0,
        "workload": 2,
        "available": true
      },
      {
        "id": 4,
        "name": "David Rodriguez",
        "email": "david.rodriguez@company.com",
        "department": "Cyber Insurance",
        "specializations": ["cyber", "technology"],
        "max_coverage_limit": 3000000.0,
        "workload": 1,
        "available": true
      }
    ],
    "SENIOR": [
      {
        "id": 1,
        "name": "Sarah Johnson",
        "email": "sarah.johnson@company.com",
        "department": "Cyber Insurance",
        "specializations": ["cyber", "technology", "professional_liability"],
        "max_coverage_limit": 10000000.0,
        "workload": 5,
        "available": true
      },
      {
        "id": 2,
        "name": "Michael Chen",
        "email": "michael.chen@company.com",
        "department": "Cyber Insurance",
        "specializations": ["cyber", "data_breach", "business_interruption"],
        "max_coverage_limit": 15000000.0,
        "workload": 7,
        "available": true
      }
    ],
    "PRINCIPAL": [
      {
        "id": 5,
        "name": "Jennifer Liu",
        "email": "jennifer.liu@company.com",
        "department": "Cyber Insurance",
        "specializations": ["cyber", "enterprise", "complex_risks"],
        "max_coverage_limit": 50000000.0,
        "workload": 3,
        "available": true
      }
    ],
    "MANAGER": [
      {
        "id": 6,
        "name": "Robert Taylor",
        "email": "robert.taylor@company.com",
        "department": "Cyber Insurance",
        "specializations": ["cyber", "management", "escalation"],
        "max_coverage_limit": 100000000.0,
        "workload": 1,
        "available": true
      }
    ]
  },
  "summary": {
    "JUNIOR": 2,
    "SENIOR": 2,
    "PRINCIPAL": 1,
    "MANAGER": 1
  }
}
```

### 3. Get Assignment Options for Work Item
**GET** `/api/workitems/{work_item_id}/assignment-options`

Returns available underwriters for reassigning a specific work item, categorized by escalation, lateral, or delegation options.

**Response Example:**
```json
{
  "work_item_id": 123,
  "current_assignment": {
    "id": 3,
    "name": "Emma Wilson",
    "email": "emma.wilson@company.com",
    "level": "JUNIOR",
    "department": "Cyber Insurance",
    "workload": 2
  },
  "recommendations": {
    "escalation": [
      {
        "id": 1,
        "name": "Sarah Johnson",
        "email": "sarah.johnson@company.com",
        "level": "SENIOR",
        "department": "Cyber Insurance",
        "workload": 5,
        "available": true,
        "specializations": ["cyber", "technology", "professional_liability"]
      },
      {
        "id": 5,
        "name": "Jennifer Liu",
        "email": "jennifer.liu@company.com",
        "level": "PRINCIPAL",
        "department": "Cyber Insurance",
        "workload": 3,
        "available": true,
        "specializations": ["cyber", "enterprise", "complex_risks"]
      }
    ],
    "lateral": [
      {
        "id": 4,
        "name": "David Rodriguez",
        "email": "david.rodriguez@company.com",
        "level": "JUNIOR",
        "department": "Cyber Insurance",
        "workload": 1,
        "available": true,
        "specializations": ["cyber", "technology"]
      }
    ],
    "delegation": []
  },
  "summary": {
    "escalation_options": 2,
    "lateral_options": 1,
    "delegation_options": 0
  }
}
```

### 4. Reassign Work Item to Different Underwriter
**PUT** `/api/workitems/{work_item_id}/reassign`

Reassigns a work item to a different underwriter with audit logging.

**Request Body:**
```json
{
  "new_underwriter_id": 1,
  "reason": "Escalating to Senior underwriter for complex risk assessment"
}
```

**Response Example:**
```json
{
  "success": true,
  "message": "Work item reassigned from emma.wilson@company.com (JUNIOR) to Sarah Johnson (SENIOR)",
  "details": {
    "work_item_id": 123,
    "old_underwriter": {
      "email": "emma.wilson@company.com",
      "name": "Emma Wilson",
      "level": "JUNIOR"
    },
    "new_underwriter": {
      "id": 1,
      "email": "sarah.johnson@company.com",
      "name": "Sarah Johnson",
      "level": "SENIOR",
      "department": "Cyber Insurance"
    },
    "reason": "Escalating to Senior underwriter for complex risk assessment",
    "timestamp": "2024-03-15T10:30:00Z"
  }
}
```

## Underwriter Experience Levels

The system supports four experience levels with different capabilities:

| Level | Description | Max Coverage | Typical Use Cases |
|-------|-------------|--------------|-------------------|
| **JUNIOR** | Entry-level underwriters | Up to $3M | Small business, standard cyber policies |
| **SENIOR** | Experienced underwriters | Up to $15M | Complex risks, technology companies |
| **PRINCIPAL** | Senior specialists | Up to $50M | Enterprise clients, high-value policies |
| **MANAGER** | Team leads and escalation | Up to $100M | Management oversight, complex approvals |

## Workflow Recommendations

### Escalation Scenarios
- **Junior → Senior**: Complex risk factors identified
- **Senior → Principal**: High coverage limits or enterprise clients
- **Principal → Manager**: Policy exceptions or unusual circumstances

### Lateral Assignment
- **Same level**: Workload balancing or specialization matching
- **Coverage within limits**: Keep at current level if underwriter has capacity

### Delegation (when appropriate)
- **Senior → Junior**: Routine renewals or standard small business policies
- **Principal → Senior/Junior**: Training opportunities for simpler cases

## Error Handling

All endpoints return appropriate HTTP status codes:

- **200**: Success
- **400**: Bad request (invalid underwriter, inactive user, etc.)
- **404**: Work item or underwriter not found
- **500**: Internal server error

Example error response:
```json
{
  "detail": "Selected underwriter is not active"
}
```

## Notes for UI Team

1. **Availability Indicator**: Use the `available` field to show green/yellow/red status
2. **Workload Display**: Show current workload numbers to help with assignment decisions
3. **Specialization Matching**: Display specializations to help match work items appropriately
4. **Audit Trail**: All reassignments are logged in the submission history
5. **Real-time Updates**: Workload counts update automatically after reassignment

## Default Underwriters Setup

The system comes pre-configured with these default underwriters:

- **Sarah Johnson** (Senior) - Cyber, Technology, Professional Liability
- **Michael Chen** (Senior) - Cyber, Data Breach, Business Interruption  
- **Emma Wilson** (Junior) - Cyber, Small Business
- **David Rodriguez** (Junior) - Cyber, Technology
- **Jennifer Liu** (Principal) - Cyber, Enterprise, Complex Risks
- **Robert Taylor** (Manager) - Cyber, Management, Escalation

All are in the "Cyber Insurance" department and can be reassigned as needed.