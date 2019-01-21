##
## BAC Stats 
## Simeon Quant
## 19.01.2019
##

library(gmodels)
library(MASS)

##
## enter data in the following order
##
## condition 1 <# of state 1> <# of state 2>
## condition 2 <# of state 1> <# of state 2>
##
## Example with the data below
##       l_silence l_noise
## RIGHT        87      70
## WRONG        13      30
##

# data from the accuracy test in silence and noise
l_silence <- c(87,13)
l_noise <- c(70,30)
left <- cbind(l_silence, l_noise)
rownames(left) <- c("RIGHT", "WRONG")

b_silence <- c(86,14)
b_noise <- c(76,24)
blinker <- cbind(b_silence, b_noise)
rownames(blinker) <- c("RIGHT", "WRONG")

s_silence <- c(81,19)
s_noise <- c(83,17)
schalte <- cbind(s_silence, s_noise)
rownames(schalte) <- c("RIGHT", "WRONG")

## Chisquare analysis of the three data sets from silence and noise

CrossTable(left, fisher = TRUE, chisq = TRUE, expected = TRUE, sresid = TRUE, format = "SPSS")
CrossTable(blinker, fisher = TRUE, chisq = TRUE, expected = TRUE, sresid = TRUE, format = "SPSS")
CrossTable(schalte, fisher = TRUE, chisq = TRUE, expected = TRUE, sresid = TRUE, format = "SPSS")

