# Example: Number classification with control flow

num = 15

if (num > 0) {
    if (num % 2 == 0) {
        type = "positive even"
    } else {
        type = "positive odd"
    }
} elif (num < 0) {
    type = "negative"
} else {
    type = "zero"
}

output = "The number ${num} is ${type}"
return output
