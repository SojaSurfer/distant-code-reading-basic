# PCA

# load libraries
library(readxl)
library(ggplot2)
library(factoextra)
library(dplyr)

# load tf-idf-dtm
tfidf <- read_excel("C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/relative_frequencies/command_tokens/tf_idf/tf_idf.xlsx")

# remove non numeric columns
tfidf_num <- tfidf %>%
  select(-game_id, -name)

tfidf_matrix <- as.matrix(tfidf_num)

# use z-scale to standardize the variables
tfidf_matrix.scale <- data.frame(scale(tfidf_matrix))

# attach row names acccording to tf-idf
rowname <- data.frame(tfidf)
row.names(tfidf_matrix) <- rowname$game_id
row.names(tfidf_matrix.scale) <- rowname$game_id

# run pca
tfidf_matrix.pca <- PCA(tfidf_matrix.scale,
                        scale.unit = F,
                        ncp = 5,
                        graph = F)

# plot a screeplot to determine how many PCs to consider analyzing
fviz_eig(tfidf_matrix.pca,
         addlabels = TRUE,
         barfill = "#1B9E77FF") +
  theme_gray()

# plot PC contribution as bar plot
fviz_contrib(tfidf_matrix.pca,
             choice = "var",
             axes = 1,
             #axes = 2,
             #axes = 3,
             top = 20,
             fill = "#1B9E77FF")+
  theme_gray()

# plot biplot
biplot <- fviz_pca_biplot(tfidf_matrix.pca, repel = TRUE,
                          axes = c(1,2),
                          #axes = c(1,3),
                          #axes = c(2,3),
                          col.var = "#1B9E77FF",
                          col.ind = "#D95F02FF",
                          geom.ind = "text",
                          select.var = list(contrib = 20),
                          pointsize = 0.5,
                          arrows = FALSE,
                          alpha.var = 0.5,
                          alpha.ind = 1) +
  theme_gray()

print(biplot)
