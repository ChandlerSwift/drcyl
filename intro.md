# Dr. CYL

Your computer has viruses! However, we've found that you can destroy them by
putting four or more viruses or pills in a row! 

## Rules

Get four in a row to destroy viruses and/or pills. Combos lead to higher
scores!

## Motion

Available moves: `left`, `right` (translation of the pill left-to-right),
`down`, `hard_drop` (equivalent to sending `down` until the pill gets as
far as it can go, but in fewer moves), `rotate_cw`, and `rotate_ccw`.

Moving left or right, or attempting to rotate when no rotation is possible,
doesn't have any effect. However, you have a limited number of turns to score
points, so try to avoid wasting them on moves that don't do anything!

Like in the original game, even when the pill is zero spaces away from (that is,
touching) a pill or virus below, it can still slide around on it. To place the
piece, move `down` (or `hard_drop`) one additional time.

To accomodate a turn-based format, the pills do not drop on their own. You have
full control over the speed they descend; however, you want to get points as
quickly as possible, so don't hesitate for too many turns!

When you place a piece, you may destroy some pills. If you get a combo, or if
pills need to fall, this may take a few turns to settle out, but will be worth
additional points.

## Sensors

Robot can access three types of information: variables, distance sensors, and configurable point sensors.

### Internal variables

Your robot has access to two internal variables:

`hp` -- your current number of hitpoints. You cannot have more than 10 HP.

`flying` -- your height above ground. You won't hit obstacles as long as flying is greater than 0. You fall one unit per turn.

### Distance sensors

Distance sensors tell you the `x` and `y` distance to the closest heart (`heart_x` and `heart_y`), coin (`coin_x` and `coin_y`), jump (`jump_x` and `jump_y`), or house (`house_x` and `house_y`). Just because it is the closest doesn't mean you can get to it. If there is no object in question (e.g., no house on the map) the sensors are set to `0`.

For historical reasons, the coordinates (0,0) represent the upper-left corner of the screen in many graphics applications. This means that a negative `object_x` value means the object is to your left (west) and a negative `object_y` value means the object is ahead of you (to the north).

## #Configurable point sensors

Your robot has seven configurable point sensors (`s1`, `s2`, `s3`, `s4`, `s5`, `s6`, and `s7`) that tell you what is located at that point on the map. Common values include: `0` (snow), `rock`, `tree`, `snowman`, `coin`, `heart`, `house`, or `jump`.

You can choose where you want the sensor to "look" (relative to your own position) by setting the variables `sNx` and `sNy` (where `N` is the sensor number 1-7). For example, if you set `s1x` to 0 and `s1y` to -1, the sensor `s1` will tell you what is directly ahead of you. See the sample code for other examples.
