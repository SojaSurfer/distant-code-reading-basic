# line visualizer
# Load libraries
library(readxl)
library(dplyr)
library(ggplot2)

# Path to table
dtm_file <- "C:/Users/Philipp/Desktop/Digital Humanities/2. Semester/Projektarbeit/token_frequencies/tokens_per_line/test/global_line_counts_table_merged.xlsx"

# Read DTM
dtm <- read_excel(dtm_file)

# grab correct column
line_count_data <- dtm %>% select(line_count)
head(line_count_data)

# histogram plot
ggplot(line_count_data, aes(x = line_count)) +
  geom_histogram(bins = 10, fill = "#1B9E77FF", color = "white") +
  labs(title = "Line count per Program",
       x = "Number of lines",
       y = "Frequency") +
  scale_x_continuous(breaks = seq(0, max(line_count_data$line_count), by = 100)) +
  theme_gray()

# boxplot
ggplot(line_count_data, aes(y = line_count)) +
  geom_boxplot(fill = "#1B9E77FF", color = "black") +
  labs(title = "Boxplot of Line Count per Program",
       y = "Line Count") +
  theme_gray()  + # Apply the gray theme
  theme(axis.title.x = element_blank(),
        axis.text.x = element_blank())

# density plot
ggplot(line_count_data, aes(x = line_count)) +
  geom_density(fill = "#1B9E77FF", alpha = 0.5) +
  labs(title = "Density Plot of Line Count per Program",
       x = "Number of Lines",
       y = "Density") +
  scale_y_continuous(labels = scales::label_number()) +
  theme_gray()
