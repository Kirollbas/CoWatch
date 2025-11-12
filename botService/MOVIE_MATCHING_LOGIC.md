# Movie Matching Logic Implementation

## Overview

This document describes the implemented logic for automatically matching users when they express interest in movies, and creating rooms when sufficient participants are found.

## Core Flow

When a user adds a movie (via `/add_movie` command), the following logic is executed:

### 1. Movie Interest Handler (`handle_movie_interest`)

Located in `bot/handlers/movie.py`, this is the main entry point that:

1. **Finds Compatible Slots**: Uses `MatchingService.find_compatible_slots()` to find existing slots for the movie that are compatible with the user's rating
2. **Checks Auto-Join Eligibility**: Uses `MatchingService.find_best_slot_for_auto_join()` to determine if the user should be automatically joined to a slot
3. **Handles Room Creation**: If auto-joining results in enough participants, creates a room using `RoomManager.create_room_for_slot()`
4. **Provides User Options**: If no auto-join occurs, shows compatible slots or standard movie actions

### 2. Matching Service (`bot/services/matching.py`)

#### Key Methods:

- **`find_compatible_slots(db, movie_id, user_id, rating_tolerance=1.0)`**
  - Finds slots where user's rating is compatible with existing participants
  - Default tolerance: ±1.0 rating points
  - Excludes slots where user is already participating
  - Excludes full slots
  - Returns slots sorted by compatibility score

- **`find_best_slot_for_auto_join(db, movie_id, user_id)`**
  - Determines if user should be automatically joined to a slot
  - Criteria:
    - User must have ratings (total_ratings > 0)
    - Slot must be close to minimum participants (within 1 participant)
    - OR user rating must be very compatible (±0.5 rating points)

- **`_is_rating_compatible(db, slot, user, tolerance=1.0)`**
  - Checks if user's rating is within tolerance of slot participants' average rating
  - Returns True if slot has no participants (anyone can join)

- **`_calculate_compatibility_score(db, slot, user)`**
  - Calculates compatibility score (lower = better)
  - Based on difference between user rating and participants' average rating

### 3. Room Manager (`bot/services/room_manager.py`)

#### Key Methods:

- **`should_create_room(slot)`**
  - Checks if room should be created for a slot
  - Criteria: participants >= min_participants AND status == "open" AND no existing room

- **`create_room_for_slot(db, slot)`**
  - Creates room in database
  - Updates slot status to "full"
  - Logs room creation details
  - Returns created room object

- **`notify_participants(context, room, message)`**
  - Sends notifications to all participants about room creation
  - Handles notification failures gracefully

- **`get_room_creation_message(room)`**
  - Generates formatted message for room creation notification
  - Includes movie title, time, participant count, and instructions

### 4. Enhanced User Experience

#### Keyboard Improvements (`bot/utils/keyboards.py`)

- **Compatible Slots Keyboard**: Shows up to 3 most compatible slots with star indicators
- **Enhanced Slot Display**: Shows compatibility indicators (⭐) for slots with compatible participants
- **Separator Handling**: Prevents errors from separator buttons in keyboards

#### User Flow Examples

**Scenario 1: Auto-Join and Room Creation**
1. User adds movie interest
2. System finds compatible slot with 2/3 participants
3. User is auto-joined (now 3/3 participants)
4. Room is automatically created
5. All participants receive notification

**Scenario 2: Compatible Slots Available**
1. User adds movie interest
2. System finds compatible slots but no auto-join
3. User sees movie info + compatible slots with ⭐ indicators
4. User can choose to join a compatible slot or create new one

**Scenario 3: No Compatible Slots**
1. User adds movie interest
2. No compatible slots found
3. User sees standard movie actions (create slot, find all slots)

## Rating Compatibility Logic

### Rating Tolerance Levels

- **Auto-Join**: ±0.5 rating points (strict compatibility)
- **Compatible Slots**: ±1.0 rating points (moderate compatibility)
- **New Users**: Users with no ratings (total_ratings = 0) are not auto-joined but can manually join any slot

### Compatibility Calculation

```python
# Example: User rating = 4.2, Slot participants average = 4.5
compatibility_score = abs(4.2 - 4.5) = 0.3
is_compatible = 0.3 <= 1.0  # True (within tolerance)
should_auto_join = 0.3 <= 0.5  # True (within strict tolerance)
```

## Database Changes

No schema changes were required. The logic uses existing models:
- `User` (with rating and total_ratings fields)
- `Movie`, `Slot`, `SlotParticipant`
- `Room` (created when conditions are met)

## Testing

The implementation includes a comprehensive test script (`test_logic.py`) that verifies:

1. ✅ Compatible slot finding for users with similar ratings
2. ✅ Auto-join logic for compatible users
3. ✅ Exclusion of incompatible users (different ratings)
4. ✅ Room creation when minimum participants reached
5. ✅ Proper participant counting and slot status updates

## Future Enhancements

The current implementation provides stubs for:
- **Telegram Group Creation**: Real Telegram group/topic creation
- **Scheduled Reminders**: Notifications before movie time
- **Discussion Management**: Automated discussion and rating phases
- **Advanced Matching**: More sophisticated compatibility algorithms

## Configuration

Key configuration options in `bot/config.py`:
- `MIN_PARTICIPANTS_DEFAULT`: Default minimum participants for slots (default: 2)

## Error Handling

The implementation includes comprehensive error handling:
- Database transaction rollbacks on failures
- Graceful handling of notification failures
- Validation of user states and slot conditions
- Logging of all major operations and errors