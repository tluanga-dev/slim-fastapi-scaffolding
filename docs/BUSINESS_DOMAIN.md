# Business Domain Documentation

## Overview

The Rental Management System is designed to handle the complete lifecycle of rental and sales operations for businesses that manage physical inventory across multiple locations. This document details the business domain, rules, workflows, and key concepts.

## Business Context

### Target Market
- Equipment rental companies
- Party/event rental businesses
- Construction equipment rental
- Electronics/appliance rental stores
- Any business with rentable inventory

### Core Value Propositions
1. **Unified Inventory Management**: Track items across multiple locations
2. **Flexible Transaction Support**: Handle both rentals and direct sales
3. **Customer Relationship Management**: Build long-term customer relationships
4. **Financial Control**: Manage deposits, fees, and payment tracking
5. **Operational Efficiency**: Streamline rental returns and inspections

## Domain Model Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Rental Business Domain                  │
├─────────────────┬─────────────────┬────────────────────────┤
│    Customers    │    Inventory    │     Transactions       │
├─────────────────┼─────────────────┼────────────────────────┤
│  - Individual   │  - Items        │  - Sales               │
│  - Business     │  - Units        │  - Rentals             │
│  - Tiers        │  - Locations    │  - Returns             │
│  - Credit       │  - Conditions   │  - Payments            │
└─────────────────┴─────────────────┴────────────────────────┘
```

## Core Business Concepts

### 1. Customer Management

#### Customer Types
- **Individual Customers**: B2C customers with personal information
- **Business Customers**: B2B customers with company information

#### Customer Tiers
Customers are classified into tiers based on their value and history:
- **Bronze**: New or low-value customers
- **Silver**: Regular customers with good history
- **Gold**: High-value customers with excellent history
- **Platinum**: VIP customers with exceptional value

#### Blacklist Management
Customers can be flagged with different risk levels:
- **Clear**: Good standing, can transact normally
- **Warning**: Some concerns, may have restrictions
- **Blacklisted**: Cannot create new transactions

#### Business Rules
1. Blacklisted customers cannot create new transactions
2. Customer tier affects pricing and available services
3. Credit limits enforce maximum exposure per customer
4. Business customers require tax ID for invoicing
5. Email and phone are required for all customers

### 2. Inventory Management

#### Item Classification
Items represent the products available for rent or sale:
- **Rental Only**: Items only available for rental
- **Sale Only**: Items only available for purchase
- **Both**: Items available for both rental and sale

#### Pricing Structure
Each item can have multiple pricing components:
- **Purchase Price**: Cost to acquire the item
- **Rental Rates**: Daily, weekly, and monthly rates
- **Sale Price**: Price for direct sale
- **Security Deposit**: Required deposit for rentals

#### Inventory Tracking
The system tracks individual units of items:
- **Serial Numbers**: Unique identification for high-value items
- **Conditions**: New, Excellent, Good, Fair, Poor, Damaged
- **Status**: Available, Rented, Sold, Maintenance, Damaged, Retired
- **Location**: Current physical location of the unit

#### Stock Management
- **Reorder Points**: Automatic alerts when stock is low
- **Multiple Locations**: Track quantities per location
- **Reserved Stock**: Items reserved for upcoming rentals
- **Available Stock**: Items ready for immediate use

### 3. Transaction Processing

#### Transaction Types
- **Sale**: Direct sale of inventory items
- **Rental**: Temporary use with return expectation
- **Return**: Processing of rental returns
- **Exchange**: Swapping one item for another
- **Refund**: Money return to customer
- **Adjustment**: Inventory corrections
- **Purchase**: Buying from suppliers

#### Transaction Lifecycle

```
Draft → Pending → Confirmed → In Progress → Completed
   ↓        ↓          ↓            ↓           ↓
   └────────┴──────────┴────────────┴───────────┴──→ Cancelled
```

#### Payment Processing
- **Multiple Payment Methods**: Cash, card, transfer, check
- **Partial Payments**: Support for installments
- **Deposit Handling**: Separate tracking of security deposits
- **Late Payment Fees**: Automatic calculation

### 4. Rental Operations

#### Rental Workflow

```
1. Customer Selection & Validation
   ├─ Check blacklist status
   ├─ Verify credit limit
   └─ Confirm contact info
   
2. Item Selection & Availability
   ├─ Check item availability
   ├─ Verify rental period allowed
   └─ Calculate pricing
   
3. Transaction Creation
   ├─ Create rental transaction
   ├─ Set rental dates
   └─ Calculate fees & deposits
   
4. Payment Processing
   ├─ Collect rental fees
   ├─ Collect security deposit
   └─ Issue receipt
   
5. Item Delivery/Pickup
   ├─ Update inventory status
   ├─ Record serial numbers
   └─ Document condition
   
6. Rental Period Monitoring
   ├─ Track due dates
   ├─ Send reminders
   └─ Calculate late fees
   
7. Return Processing
   ├─ Receive items
   ├─ Inspect condition
   └─ Process final charges
   
8. Transaction Completion
   ├─ Release deposits
   ├─ Update inventory
   └─ Close transaction
```

#### Return Processing

##### Return Types
- **Full Return**: All items returned
- **Partial Return**: Some items returned, others kept/extended

##### Inspection Process
1. **Physical Inspection**: Check for damage or missing parts
2. **Condition Assessment**: 
   - None: No damage
   - Minor: Cosmetic damage only
   - Moderate: Functional but needs repair
   - Major: Significant damage
   - Total Loss: Item destroyed/missing
3. **Fee Calculation**: Based on damage level and repair costs
4. **Deposit Resolution**: Release or apply to damages

### 5. Supplier Management

#### Supplier Types
- **Manufacturer**: Original equipment manufacturers
- **Distributor**: Regional distributors
- **Wholesaler**: Bulk suppliers
- **Retailer**: Retail suppliers for small quantities
- **Service**: Maintenance and repair providers

#### Supplier Relationships
- **Performance Tracking**: Quality and delivery ratings
- **Payment Terms**: NET15, NET30, NET45, etc.
- **Credit Management**: Track amounts owed
- **Contract Management**: Start/end dates, terms

### 6. Financial Management

#### Revenue Streams
1. **Rental Income**: Daily/weekly/monthly rental fees
2. **Sales Revenue**: Direct sales of inventory
3. **Late Fees**: Penalties for overdue returns
4. **Damage Fees**: Charges for damaged items
5. **Service Fees**: Additional services (delivery, setup)

#### Cost Management
1. **Purchase Costs**: Acquiring inventory
2. **Maintenance Costs**: Keeping items in good condition
3. **Storage Costs**: Warehouse and location expenses
4. **Operational Costs**: Staff, utilities, etc.

#### Deposit Management
- **Collection**: At rental initiation
- **Holding**: During rental period
- **Application**: To damages or fees
- **Release**: Return to customer

## Key Business Workflows

### 1. New Customer Onboarding

```
1. Capture customer information
   - Type (Individual/Business)
   - Contact details
   - Identification/Tax ID
   
2. Perform background checks
   - Credit check (if applicable)
   - Previous rental history
   - Reference verification
   
3. Assign customer tier
   - Based on initial assessment
   - Set initial credit limit
   
4. Create customer record
   - Generate customer ID
   - Set up communication preferences
```

### 2. Inventory Procurement

```
1. Identify need
   - Low stock alert
   - New product requirement
   - Replacement need
   
2. Supplier selection
   - Compare prices
   - Check availability
   - Review performance
   
3. Purchase order creation
   - Select items and quantities
   - Negotiate terms
   - Submit order
   
4. Receiving process
   - Verify quantities
   - Check quality
   - Create inventory units
   
5. Distribution
   - Allocate to locations
   - Update stock levels
   - Make available for rent/sale
```

### 3. Rental Extension

```
1. Customer request
   - Before or during rental period
   - Check item availability
   
2. Validation
   - No other reservations
   - Customer in good standing
   - Payment up to date
   
3. Extension processing
   - Update end date
   - Calculate additional fees
   - Process payment
   
4. Communication
   - Confirm with customer
   - Update internal records
   - Notify relevant staff
```

### 4. Damage Claim Process

```
1. Damage identification
   - During return inspection
   - Document with photos
   - Assess severity
   
2. Cost estimation
   - Repair costs
   - Replacement value
   - Lost rental income
   
3. Customer communication
   - Notify of damage
   - Provide evidence
   - Discuss resolution
   
4. Financial resolution
   - Apply deposit
   - Charge additional fees
   - Payment plan if needed
   
5. Item disposition
   - Schedule repairs
   - Update condition
   - Return to inventory or retire
```

## Business Rules and Constraints

### Customer Rules
1. **Blacklist Enforcement**: Blacklisted customers cannot create new transactions
2. **Credit Limit**: Total exposure cannot exceed credit limit
3. **Required Fields**: 
   - Individual: First name, last name, email, phone
   - Business: Business name, tax ID, email, phone
4. **Tier Benefits**: Higher tiers get better rates and priority service

### Inventory Rules
1. **Availability**: Items can only be rented if status is "Available"
2. **Minimum Rental**: Items may have minimum rental periods
3. **Maximum Rental**: Items may have maximum rental periods
4. **Condition Standards**: Items below "Fair" condition cannot be rented
5. **Serial Tracking**: High-value items must have serial numbers

### Transaction Rules
1. **Status Transitions**: Must follow defined workflow
2. **Payment Requirements**: 
   - Sales: Full payment before completion
   - Rentals: Deposit + first period payment
3. **Return Window**: Returns must be processed within grace period
4. **Cancellation**: Only possible before "In Progress" status

### Financial Rules
1. **Deposit Calculation**: Based on item value and customer tier
2. **Late Fees**: Calculated daily after grace period
3. **Damage Assessment**: Must be documented with evidence
4. **Refund Policy**: Follows business-defined rules

## Performance Indicators (KPIs)

### Operational KPIs
- **Utilization Rate**: % of inventory currently rented
- **Turnaround Time**: Average time to process returns
- **Availability Rate**: % of time items are available
- **Damage Rate**: % of rentals with damage claims

### Financial KPIs
- **Revenue per Location**: Track location performance
- **Average Transaction Value**: Monitor transaction sizes
- **Collection Rate**: % of fees collected on time
- **Deposit Resolution**: % released vs applied to damages

### Customer KPIs
- **Customer Lifetime Value**: Total revenue per customer
- **Retention Rate**: % of repeat customers
- **Tier Distribution**: Customer distribution across tiers
- **Satisfaction Score**: From feedback and reviews

## Integration Points

### External Systems
1. **Payment Processors**: Credit card and online payments
2. **Accounting Software**: Financial data export
3. **CRM Systems**: Customer data synchronization
4. **Shipping Providers**: Delivery tracking
5. **Insurance Providers**: Coverage verification

### Communication Channels
1. **Email**: Confirmations, reminders, receipts
2. **SMS**: Urgent notifications, reminders
3. **Web Portal**: Customer self-service
4. **Mobile App**: Field operations

## Compliance and Regulations

### Data Protection
- **PII Handling**: Secure storage of personal information
- **Payment Data**: PCI compliance for card processing
- **Data Retention**: Follow legal requirements
- **Right to Delete**: Support GDPR/CCPA requirements

### Financial Compliance
- **Tax Calculation**: Accurate tax application
- **Invoice Requirements**: Legal invoice format
- **Audit Trail**: Complete transaction history
- **Financial Reporting**: Support for audits

### Industry Specific
- **Safety Standards**: Equipment meets safety requirements
- **Age Verification**: For restricted items
- **Insurance Requirements**: Adequate coverage
- **Licensing**: Proper business licenses

## Future Enhancements

### Advanced Features
1. **Predictive Analytics**: Demand forecasting
2. **Dynamic Pricing**: Market-based pricing
3. **Route Optimization**: Delivery planning
4. **Maintenance Scheduling**: Preventive maintenance
5. **Customer Portal**: Self-service capabilities

### Business Expansion
1. **Franchise Support**: Multi-tenant architecture
2. **B2B Marketplace**: Inter-business rentals
3. **Subscription Rentals**: Monthly subscriptions
4. **International**: Multi-currency and language

---

This business domain model provides a comprehensive foundation for understanding and implementing the rental management system's business logic and workflows.