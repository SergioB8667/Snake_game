import turtle
import time
import random

delay = 0.1
score = 0
segments = [] # This list will hold the body parts
# 1. Set up the screen
wm = turtle.Screen()
wm.title("Snake Game")
wm.bgcolor("black")
wm.setup(width=600, height=600)
wm.tracer(0) # Turns off screen updates for smoother animation

# 2. Snake Head
head = turtle.Turtle()
head.speed(0)
head.shape("square")
head.color("green")
head.penup()
head.goto(0,0)
head.direction = "stop"

# 3. Snake Food
food = turtle.Turtle()
food.speed(0)
food.shape("circle")
food.color("red")
food.penup()
food.goto(0,100)

# 4. Movement Functions
def go_up():
    if head.direction != "down":
        head.direction = "up"
def go_down():
    if head.direction != "up":
        head.direction = "down"
def go_left():
    if head.direction != "right":
        head.direction = "left"
def go_right():
    if head.direction != "left":
        head.direction = "right"

def move():
    if head.direction == "up":
        y = head.ycor()
        head.sety(y + 20)
    if head.direction == "down":
        y = head.ycor()
        head.sety(y - 20)
    if head.direction == "left":
        x = head.xcor()
        head.setx(x - 20)
    if head.direction == "right":
        x = head.xcor()
        head.setx(x + 20)

# 5. Keyboard Bindings
wm.listen()
wm.onkey(go_up, "w")
wm.onkey(go_down, "s")
wm.onkey(go_left, "a")
wm.onkey(go_right, "d")

# 6. Main Game Loop
while True:
    wm.update()

    # Check for collision with food
    if head.distance(food) < 20:
        # Move food to random spot
        x = random.randint(-280, 280)
        y = random.randint(-280, 280)
        food.goto(x, y)

        # ADD A SEGMENT (This makes the snake grow)
        new_segment = turtle.Turtle()
        new_segment.speed(0)
        new_segment.shape("square")
        new_segment.color("grey")
        new_segment.penup()
        segments.append(new_segment)

    # Move the end segments first in reverse order
    for index in range(len(segments)-1, 0, -1):
        x = segments[index-1].xcor()
        y = segments[index-1].ycor()
        segments[index].goto(x, y)

    # Move segment 0 to where the head is
    if len(segments) > 0:
        x = head.xcor()
        y = head.ycor()
        segments[0].goto(x, y)

    move()
    
    # Check for wall collisions
    if head.xcor()>290 or head.xcor()<-290 or head.ycor()>290 or head.ycor()<-290:
        time.sleep(1)
        head.goto(0,0)
        head.direction = "stop"
        # Hide segments and clear list
        for segment in segments:
            segment.goto(1000, 1000)
        segments.clear()

    time.sleep(delay)
    
