# Example 10: Factorial calculator with Version 2 features

n = 5
x = n
fact = 1

if (x > 0) {
    while (x > 1) {
        fact = fact * x
        x = x - 1
    }
    output = "Factorial of ${n} is ${fact}"
} else {
    output = "${n} is not a positive number"
}
return output
