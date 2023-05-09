# airplane_boarding
Simulates the process of boarding a plane. Can I determine the fastest way to board a plane?

## Running
Sitting in the Montreal airport (YUL) waiting to board my return flight on January 4th, 2023, I thought to myself, "Holy this is taking a long time!" It was. On a flight supposed to board at 5:40 PM, we didn't even begin boarding until 6:30 PM. The flight didn't take off until 7:15 PM. 45-minute boarding time felt a bit much. I wondered: "Was there a faster way to board a plane?" This thought brought me back to a CGP Grey YouTube video, ["The Better Boarding Method Airlines Won't Use"](https://www.youtube.com/watch?v=oAHbLRjF0vo). I remarked to my dad, "I bet I could make a simulation out of this to find out which boarding method is the fastest!" And so, here I am.

Run with:
```
python ~/airplane_boarding/airplane_boarding.py window_width window_height
```
where \* :
- `window_width` is the desired width of window (in pixels). This must be an integer value, though it is not necessary.
- `window_height` is the desired height of window (in pixels). This must be an integer value, though it is also not necessary.

\* If no arguments are provided, the program will resort to the defaults that worked for my device.

## Seat Layouts
Various characteristics of the simulated plane can be altered. This can be done by changing values in the `seat_layouts` table, defined in line `48`. Here are some of those characteristics:
- The user can set the number of exits on the plane with `n_exits`. Users can choose for the plane to have `1`, `2`, or `3` exits. This value is defined on line `47`.
- Remove/add a row from `seat_layouts` to remove/add that section from the plane. For instance, if the user doesn't want a first class, simply remove the row associated with `first`.
- Alter the values in the `seat_layout` column to change the seat layout. Place seats in alphabetical order; spaces denote walkways. The number of walkways must be equal for each section of the plane, or an `n_walkways exception` is thrown. There must be at least one walkway and at most two, and if this rule is violated, an `n_walkways exception` is also thrown.
- `n_rows` indicates the number of rows in each section. This value must be between 5 and 50 (inclusive).
- `leg_room` is the leg room for each section in terms of passenger diameters. For instance, a value of `1.5` is a leg room of one and a half times a passenger's diameter.
- `seat_depth` follows a similar concept to leg_room, but refers to the depth of a seat.

Some values provided to `seat_layouts` are too extreme for the program to handle, though `airplane_boarding.py` does its best to correct any errors. If any errors are found and corrected, the program notifies the user of this in the console.

---

This is still a work in progress. I am currently coding various boarding methods. A struggle with this simulation is that with so many `tkinter` instances, the program can get really slow if I spawn too many passengers at once. Hopefully you enjoy what I have accomplished so far!
