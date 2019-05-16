##
## BAC Stats 
## Simeon Quant
## 19.01.2019
##
## V2: data from files

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

setwd("/Volumes/dahoam/Simeon/BAC/stats")
sink(file = "BAC_stats_output_V3.txt", append = FALSE, type = c("output","message"))

## data from the accuracy test in silence and noise
## Chisquare analysis of the 3 data sets from silence and noise
word <- as.matrix(read.table(file = "blinke_links.data"))
CrossTable(word, fisher = TRUE, chisq = TRUE, expected = TRUE, sresid = TRUE, format = "SPSS")

word <- as.matrix(read.table(file = "blinke_rechts.data"))
CrossTable(word, fisher = TRUE, chisq = TRUE, expected = TRUE, sresid = TRUE, format = "SPSS")

word <- as.matrix(read.table(file = "schalte_runter.data"))
CrossTable(word, fisher = TRUE, chisq = TRUE, expected = TRUE, sresid = TRUE, format = "SPSS")

sink()
