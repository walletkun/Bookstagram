from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import datetime
from django.core.exceptions import ValidationError
from mptt.models import MPTTModel, TreeForeignKey
from django.contrib.auth.models import AbstractUser

##### Book Stuff #####

# Book Table
# Uniqueness will be ensured with a hash id with authors and title.
# ManyToMany connection with authors, through normalization table, means that author entities should be created first.
class Book(models.Model):
    """Book Table

    Args:
        models (Model Object): Inheritance Model Object

    Variables:
        title: max_length of 255, not null
        summary: text summary of the book, optional
        average_rating: the average rating of the book, 0.00 - 5.00
        year_published:  Original publication date of book (first edition date).
        original_langauge: Original language of work
        book_id: Hashing normalized title and author list ensures book uniqueness.
        authors: ManyToMany relation through BookAuthor table.
    """
    title = models.CharField(
        max_length=255,
        null=False,
        )
    summary = models.TextField(
        blank=True, 
        null=True
        )
    average_rating = models.DecimalField(
        default=0.00, 
        max_digits=3, 
        decimal_places=2,
        validators = [
            MinValueValidator(0.00),
            MaxValueValidator(5.00)
        ]
        )
    year_published = models.PositiveIntegerField(
        blank=True,
        null=True,
        validators = [
            MinValueValidator(1000),
            MaxValueValidator(datetime.date.today().year + 10)
        ],
    )
    original_language = models.CharField(
        max_length = 50,
        blank = True,
        null = True
    )
    book_id = models.CharField(max_length=64, unique=True)
    authors = models.ManyToManyField("Author", through="BookAuthor")
    genres = models.ManyToManyField("Genre", through="BookGenre")

    class Meta:
        verbose_name = "Book"
        verbose_name_plural = "Books"
        ordering = ['title']
        indexes = [
            models.Index(fields = ['title']),
            models.Index(fields=['year_published']),
            models.Index(fields=['book_id'])
        ]

    def __str__(self):
        return self.title

# Author Table
# This needs work, no way to sepeate authors of the same name.
class Author(models.Model):
    """
    Author Table
    Args:
        models (Model Object): Inheritance of the Model's Object

    Variables: 
        name: name of author
        biography: Text (Optional)
        author_image: URL/Text (Optional)
    """
    name = models.CharField(max_length=250) 
    biography = models.TextField(blank=True, null=True)
    author_image = models.URLField(blank=True, null=True)
    author_id = models.CharField(max_length=64, unique=True)
    
    class Meta:
        verbose_name = "Author"
        verbose_name_plural = "Authors"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['author_id'])
        ]


    def __str__(self):
        return self.name

# Normalization table used by Book's ManyToMany relationship with Author.
class BookAuthor(models.Model):
    """
    Book Author Table

    Relationships:
    - One Book can have multiple BookAuthor entries (One to Many)
    - One Author can have multiple BookAuthor entries (One to Many)

    """
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='related_book_authors')
    author = models.ForeignKey('Author', on_delete=models.CASCADE, related_name='related_author_books')


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['book', 'author'], name='unique_book_author')
        ]
        indexes = [
            models.Index(fields=['book', 'author']),
            models.Index(fields=['author', 'book'])
        ]

    def __str__(self):
        return f"Author Name - Book Title: {self.author.name} - {self.book.title}"

# Genres Table used for Book data.
class Genre(models.Model):
    """
    Genres Table

    Variables:
        name: Unique name for each genre, max length of 100.
    """

    name = models.CharField(max_length=100, unique=True)
    class Meta:
        verbose_name = "Genre"
        verbose_name_plural = "Genres"
        ordering = ['name']
        
    def __str__(self):
        return self.name

# Normalization table used for Book's ManyToMany relationship with genre.
class BookGenre(models.Model):
    """
    Book Genre Table

    Variables:
        book: Foreign Key from Book
        genre: Foreign Key from Genre

    Class:
        Meta: Unique them together, so it prevents entries from same book-genre pair
    """
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='related_book_genres')
    genre = models.ForeignKey('Genre', on_delete=models.CASCADE, related_name='related_genre_books')

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['book', 'genre'], name='unique_book_genre')
        ]
        indexes = [
            models.Index(fields=['book', 'genre']),
            models.Index(fields=['genre', 'book'])
        ]
        ordering = ['genre__name']

    def __str__(self):
        return f"{self.book.title} - {self.genre.name}"

# Edition Table. This is the center for data uploads.
class Edition(models.Model):
    """
    Edition Table

    Variables:
        book: Foreign Key from Book Table
        isbn: unique serial code for each book, cannot be null
        publisher: Foreign Key from Publisher Table
        kind: Enum: Pick Either ['Hardcover', 'Paperback', 'ebook', 'AudioBook'], since format is a keyword lets go with kind
        publication_year: check valid year, integer
        language: max_length of 50, not null
    """

    # Formatting Choices
    FORMAT_CHOICES = [
        ('Hardcover', 'Hardcover'),
        ('Paperback', 'Paperback'),
        ('eBook', 'eBook'),
        ('Audiobook', 'Audiobook'),
        ('Other', 'Other')
        ]
    
    book = models.ForeignKey("Book", on_delete=models.CASCADE, related_name='editions')
    isbn = models.CharField(max_length=13, unique=True)
    publisher = models.ForeignKey("Publisher", on_delete=models.SET_NULL, related_name='editions', null=True, blank=True)
    kind = models.CharField(max_length=10, choices=FORMAT_CHOICES, null=False)
    is_primary = models.BooleanField(default=False)
    publication_year = models.PositiveIntegerField(
            validators=[
                MinValueValidator(1500),
                MaxValueValidator(datetime.date.today().year)]
        )
    language = models.CharField(max_length=50, null=False)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    edition_number = models.PositiveIntegerField(null=True, blank=True)
    abridged = models.BooleanField(default=False)
    class Meta:
        verbose_name = "Edition"
        verbose_name_plural = "Editions"
        ordering = ['-publication_year']
        indexes = [
            models.Index(fields=['isbn']),
            models.Index(fields=['publication_year']),
            models.Index(fields=(['kind']))
        ]

    def __str__(self):
        return f'{self.book.title} - {self.kind} - ({self.isbn}) - ({self.publication_year})'

# Publisher Table, used by edition.
class Publisher(models.Model):
    """
    Publisher Table

    Args:
        models (Model Object): Inheritance of the Model's Object

    Variables:
        name: max_length of 100, publisher's name
        contact_info: contact information for the publisher
    """
    name = models.CharField(max_length=100, unique=True)
    contact_info = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = "Publisher"
        verbose_name_plural = "Publishers"
        ordering = ['name']
        indexes = [
            models.Index(fields=['name'])
        ]

    def __str__(self):
        return self.name  

# Cover Image table connecting to edition.
class CoverImage(models.Model):
    """
    Cover Image Table

    Variables:
        edition: Foreign Key from Edition Table (One To Many Relationship)
        image_url: the cover image of the book, not null (Text)
        is_primary: if it's going to be the primary cover, (default: false)
    """
    edition = models.ForeignKey("Edition", on_delete=models.CASCADE, related_name="related_edition_image")
    image_url = models.URLField()
    is_primary = models.BooleanField(default=False)

    class Meta:
        verbose_name = "CoverImage"
        verbose_name_plural = "CoverImages"

    def __str__(self):
        return f"Book - URL - primary?: {self.edition.book} - {self.image_url} - {self.is_primary}"

##### User Stuff #####

# User Table
class User(AbstractUser):
    """
    User Table

    Inherits from Django's AbstractUser class. 
    Additional Variables:
        trust_level: User's Trust Level in terms of lending books, default 50, maximum 100, minimum 0.
        profile_pic: URL to profile image.
        books: ManyToMany relationship normalized through UserBook.
        achievements: ManyToMany relationship normalized through UserAchievements.
    """
    trust_level = models.IntegerField(
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
            ],
        default=50,
        )
    profile_pic = models.URLField(blank=True, null=True)
    books = models.ManyToManyField("Book", through="UserBook")
    achievements = models.ManyToManyField("Achievement", through="UserAchievement")

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = (
            models.Index(fields=['username']),
            models.Index(fields=['email']),
        )
        ordering = ['username']
        
# User Book Table. Normalization tabe used by User's ManyToMany relationship with Book.
class UserBook(models.Model):
    """
    User Book Table

    Variables:
        book: Foreign Key from Book (Zero to Many)
        user: Foreign Key from User (Zero to Many)
        read_status: Enum('Read', 'Reading', 'Want to Read'), defaulted to want to read
        page_num: amount of pages, default 0
        is_owned: if it's owned by anyone , boolean: default false
        date_started: optional: starting date
        date_ended: optional: date finished
    """

    # Enum for read status
    READ_STATUS_CHOICES = [
        ('Read', 'Read'),
        ('Reading', 'Reading'),
        ('Want to Read', 'Want to Read')
        ]

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='related_user_books')
    book = models.ForeignKey('Book', on_delete=models.CASCADE, related_name='related_user_books')
    read_status = models.CharField(max_length=20, choices=READ_STATUS_CHOICES, null=True, blank=True)
    page_num = models.PositiveBigIntegerField(default=0)
    is_owned = models.BooleanField(default=False)
    is_favorite = models.BooleanField(default=False)
    date_started = models.DateField(blank=True, null=True)
    date_ended = models.DateField(blank=True, null=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'book'], name='unique_user_book')
        ]
        indexes = [
            models.Index(fields=['read_status']),
            models.Index(fields=['is_owned']),
        ]


    def __str__(self):
        return f"{self.user.username} - {self.book.title} - ({self.read_status})"


# Achievement Table
class Achievement(models.Model):
    """
    Achievements Table

    Variables:
        name: name of the achievements, not null and unique and maxlength of 50
        achieve_desc: description of the achievement, TEXT
        achieve_icon: icon of the achievement, TEXT
    """

    name = models.CharField(max_length=50, null=False, unique=True)
    achieve_desc = models.TextField(blank=True, null=True)
    achieve_icon = models.URLField(blank=True, null=True)
    difficulty_lvl = models.PositiveIntegerField(blank=True, null = True)

    class Meta:
        verbose_name = "Achievement"
        verbose_name_plural = "Achievements"
        indexes = (
            models.Index(fields=['name']),
            models.Index(fields=['difficulty_lvl'])
        )
        ordering = ['name']

    def __str__(self):
        return self.name


# User Achievements Table used for normnalization in User's ManyToMany relationship with Achievement.
class UserAchievement(models.Model):
    """
    User Achievements Table

    Variables:
        user: Foreign Key from User Table
        achievement: Foreign Key from Achievement Table
        completed: achievement status, default to false, boolean
        completion_percentage: percentage of completion, default to 0.00, 5 digits and 2 decimal places
    """

    user = models.ForeignKey("User", on_delete=models.CASCADE, related_name="user_achievements")
    achievement= models.ForeignKey("Achievement", on_delete=models.CASCADE, related_name="related_achievement_users")
    completed = models.BooleanField(default=False)
    completion_percentage = models.DecimalField(default=0.00, max_digits=5, decimal_places=2)


    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'achievement'], name='unique_user_achievement')
        ]
        indexes = [
            models.Index(fields=['completed'])
        ]
        ordering = ['completion_percentage']

    def __str__(self):
        return f"{self.user} - {self.achievement} (Completed: {self.completed})"


# User Profile
class UserProfile(models.Model):
    """
    User Profile Table

    Variables:
        user: One to One relation from User (One to One)
        bio: optional: text of user's biography
        user_location: optional: maxlength of 100
        social_links: optional
    """

    user = models.OneToOneField('User', on_delete=models.CASCADE, related_name="related_user_profile")
    bio = models.TextField(null=True, blank=True)
    zip_code = models.CharField(max_length=10, blank=False, null=False, default="11210") 
    social_links = models.CharField(blank=True, null=True)

    class Meta:
        verbose_name = "UserProfile"
        verbose_name_plural = "UserProfiles"
        indexes = [
            models.Index(fields=['zip_code'])
        ]

    def __str__(self):
        return f'{self.user.username}'

# Shelf table
class Shelf (models.Model):
    """
    Shelf table

    Variables:
    user: Foriegn key: the user who the shelf belongs to.
    name: max length 250 char: the given name for shelf
    shelf_desc: text: optional: the given description.
    shelf_img: URL/text: the shelf's user ganted image url.
    is_private: boolean: default False. Represents whether shelf is maked private.
    shelf_type: ENUM: the shelf's type.
    books: ManyToMany field with Edition Table normalized through ShelfEdition.
    created_on: The date the shelf was created.
    """
    SHELF_TYPES = [
        ("Owned", "Owned"),
        ("Read", "Read"),
        ("Reading", "Reading"),
        ("Want to Read", "Want to Read"),
        ("Favorites", "Favorites"),
        ("Available", "Available"),
        ("Lent Out", "Lent Out"),
        ("Custom", "Custom"),
    ]
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="shelves")
    name = models.CharField(max_length=250)
    shelf_desc = models.TextField(null=True, blank=True)
    shelf_img = models.URLField(null=True, blank=True)
    is_private = models.BooleanField(default=False)
    shelf_type = models.CharField(max_length=20, choices=SHELF_TYPES, null=False)
    books = models.ManyToManyField("Edition", through="ShelfEdition")
    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Shelf"
        verbose_name_plural = "Shelves"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["shelf_type"])
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.user} {self.name} {self.shelf_type}"
    
class ShelfEdition(models.Model):
    """
    ShelfBook Table (Normalization Table)

    Variables:
    shelf: Foriegn key to Shelf
    edition: Foriegn key to Edition
    """
    shelf = models.ForeignKey("Shelf", on_delete=models.CASCADE, related_name="shelf_books")
    edition = models.ForeignKey("Edition", on_delete=models.CASCADE, related_name="edition_shelves")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['shelf', 'edition'], name='unique_shelf_edition')
        ]

    def __str__(self):
        return f'{self.shelf.name} - {self.edition}'

class Journal(models.Model):
    """
    Journal Model
    
    Variables:
    user_book: FK to UserBook - the user-book relationship this journal is for
    created_on: Date the journal was created
    updated_on: Date the journal was last updated
    is_private: Boolean indicating if the journal is private
    """


    user_book = models.OneToOneField(
        "UserBook", 
        on_delete=models.CASCADE,
        related_name="journal"

    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    is_private = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = "Journal"
        verbose_name_plural = "Journals"
        indexes = [
            models.Index(fields=["updated_on"]),
            models.Index(fields=["is_private"]),
        ]
        ordering = ["-updated_on"]
    
    def __str__(self):
        return f"{self.user_book.user.username}'s journal for {self.user_book.book.title}"


# Journal Entry Table for entries within a journal
class JournalEntry(models.Model):
    """
    Journal Entry Model

    Variables:
    journal: FK to Journal - the journal this entry belongs to
    title: Optional string to head journal entry
    content: Text content of the journal entry
    created_on: Date the entry was created
    updated_on: Date the entry was last updated
    page_num: Optional page number reference
    is_private: Boolean indicating if the entry is private (overrides journal privacy if True)
    """

    journal = models.ForeignKey(
        "Journal",
        on_delete=models.CASCADE,
        related_name="entries"
    )
    title = models.CharField(max_length=255, null=True, blank=True)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    page_num = models.PositiveIntegerField(null=True, blank=True)
    is_private = models.BooleanField(default=False)
    

    class Meta:
        verbose_name = "JournalEntry"
        verbose_name_plural = "JournalEntries"
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["page_num"]),
            models.Index(fields=["updated_on"]),
            models.Index(fields=["is_private"]),
        ]
        ordering = ["-updated_on"]
    
    def __str__(self):
        return f"Entry by {self.journal.user.username} on {self.journal.book.title}: {self.title or 'Untitled'}"


##### Community Stuff #####

# Review table
class Review(models.Model):
    """
    Review Table

    Variables:
        book: Foriegn key associated with book table.
        user: Foriegn key associated with user table.
        content: optional: written text of review.
        rating: decimal value 0.00-5.00 representing star rating.
        created_on: Date: date the review is created on.
        flagged_count: integer value, initialized to 0, 
            representing how many times review has been flagged as voilating TOS.
    """
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="reviews")
    book = models.ForeignKey("Book", on_delete=models.CASCADE, related_name='reviews')
    content = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    flagged_count = models.PositiveBigIntegerField(default=0)
    rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        validators=[
            MinValueValidator(0.00),
            MaxValueValidator(5.00)
        ],
    )
    class Meta:
        verbose_name = "Review"
        verbose_name_plural = "Reviews"
        indexes = [
            models.Index(fields=["created_on"]),
            models.Index(fields=["rating"]),
        ]
        ordering = ["-created_on"]

    def __str__(self):
        return f'Review by {self.user} on {self.book} - {self.rating} stars'

# Community Table
class Community(models.Model):
    """
    Community Table

    Variables:
        book: Foreign Key, 1 to 1 Relationship with Book
    """
    book = models.OneToOneField(
        Book,
        on_delete=models.CASCADE,
        related_name='related_community',
        null=True,
        blank=True
        )
    users = models.ManyToManyField("User", through="CommunityUser")

    class Meta:
        verbose_name = "Community"
        verbose_name_plural = "Communities"

    def __str__(self):
        return f"Community for {self.book.title}" if self.book else "Community (No Book)"

# CommunityFollower table. Used for normalization in Community's ManyToMany relationship with User
class CommunityUser(models.Model):
    """
    CommunityUser Table

    Variables:
        community: Foriegn Key from Community -- 
            Community has many CommunityFollowers, CommunityFollower has one Community.
        user: Foriegn Key from User --
            User has many CommunityFollowers, CommunityFollower has one User.
    """
    community = models.ForeignKey('Community', on_delete=models.CASCADE, related_name="related_users")
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name="related_communities")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['community', 'user'], name='unique_community_user')
        ]
    
    def __str__(self):
        return f"{self.user.username} in {self.community}"

# Book Club Table
class BookClub(models.Model):
    """
    Book Club Table

    Variables:
        name: One to Many relation from Club Member (One to Many)
        club_desc: optional: text description of club
        is_private: sets whether or not club is private (default FALSE)
    """

    name = models.CharField(max_length=250, null=False)
    club_desc = models.TextField(null=True, blank=True)
    is_private = models.BooleanField(default=False)
    about_content = models.TextField(
        null=True, 
        blank=True, 
        help_text="Detailed description for the club's About page, perhaps to be in markdown."
    )
    club_image = models.URLField(null=True, blank=True)
    users = models.ManyToManyField("User", through="ClubMember")
    book = models.ForeignKey(
        "Book",
        on_delete=models.CASCADE,
        related_name='related_book_club',
        null=True,
        blank=True
    )
    upcoming_book = models.ForeignKey(
        "Book",
        on_delete=models.SET_NULL,
        related_name='upcoming_in_clubs',
        null=True,
        blank=True,
    )
    created_on = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "BookClub"
        verbose_name_plural = "BookClubs"
        indexes = [
            models.Index(fields=["name"])
        ]
        ordering = ['name']

    def __str__(self):
        return self.name

# Club Member Table. Used for normalization in Club's ManyToMany relationship to user.
class ClubMember(models.Model):
    """
    Club Member Table

    Variables:
        club: Foreign Key to BookClub
        user: Foreign Key to User
        join_date: When the user joined the club
        is_admin: Whether this member has admin privileges
        reading_status: Optional status for current book
    """
    READING_STATUS_CHOICES = [
        ('Not Started', 'Not Started'),
        ('Reading', 'Reading'),
        ('Completed', 'Completed'),
        ('On Hold', 'On Hold')
    ]

    club = models.ForeignKey('BookClub', on_delete=models.CASCADE)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    join_date = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    reading_status = models.CharField(
        max_length=20, 
        choices=READING_STATUS_CHOICES,
        default='Not Started'
    )
    current_page = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'club'], name='unique_club_user')
        ]
        indexes = [
            models.Index(fields=['club', 'is_admin']),
            models.Index(fields=['reading_status'])
        ]

    def __str__(self):
        return f"{self.user.username} in {self.club.name}"
    


class BookClubHistory(models.Model):
    """
    Book Club History Table
    
    Tracks books that a book club has read in the past.
    
    Variables:
        club: Foreign Key to BookClub
        book: Foreign Key to Book (the book that was read)
        start_date: When the club started reading this book
        end_date: When the club finished reading this book
        club_rating: Optional club consensus rating for the book
        order: Chronological order in the club's reading history
    """
    club = models.ForeignKey(
        "BookClub", 
        on_delete=models.CASCADE, 
        related_name="reading_history"
    )
    book = models.ForeignKey(
        "Book", 
        on_delete=models.CASCADE, 
        related_name="read_by_clubs"
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    club_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2,
        validators=[
            MinValueValidator(0.00),
            MaxValueValidator(5.00)
        ],
        null=True,
        blank=True
    )
    order = models.PositiveIntegerField(
        default=1
    )

    class Meta:
        verbose_name = "Book Club History"
        verbose_name_plural = "Book Club Histories"
        ordering = ['club', '-end_date']
        indexes = [
            models.Index(fields=['club', 'book']),
            models.Index(fields=['end_date'])
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['club', 'book', 'order'],
                name='unique_club_book_order'
            )
        ]

    def __str__(self):
        return f"{self.club.name} - {self.book.title}"

class Announcement(models.Model):
    """
    Announcement Table
    
    For club announcements and updates.
    
    Variables:
        club: Foreign Key to BookClub
        title: Title of the announcement
        content: Text content of the announcement
        created_by: User who created the announcement
        created_on: When the announcement was created
        is_pinned: Whether the announcement should be pinned to the top
    """
    club = models.ForeignKey(
        "BookClub", 
        on_delete=models.CASCADE, 
        related_name="announcements"
    )
    title = models.CharField(max_length=250)
    content = models.TextField()
    created_by = models.ForeignKey(
        "User", 
        on_delete=models.CASCADE, 
        related_name="created_announcements"
    )
    created_on = models.DateTimeField(auto_now_add=True)
    is_pinned = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Announcement"
        verbose_name_plural = "Announcements"
        ordering = ['-is_pinned', '-created_on']
        indexes = [
            models.Index(fields=['club']),
            models.Index(fields=['created_on']),
            models.Index(fields=['is_pinned'])
        ]

    def __str__(self):
        return f"{self.club.name} - {self.title}"
    
class ReadingSchedule(models.Model):
    """
    Reading Schedule Table
    
    Defines reading goals and deadlines for book clubs.
    
    Variables:
        club: Foreign Key to BookClub
        book: Foreign Key to Book (the book being scheduled)
        start_date: When to start reading
        end_date: Target completion date
        is_active: Whether this is the currently active schedule
    """
    club = models.ForeignKey(
        "BookClub", 
        on_delete=models.CASCADE, 
        related_name="reading_schedules"
    )
    book = models.ForeignKey(
        "Book", 
        on_delete=models.CASCADE, 
        related_name="reading_schedules"
    )
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Reading Schedule"
        verbose_name_plural = "Reading Schedules"
        ordering = ['-is_active', '-start_date']
        indexes = [
            models.Index(fields=['club', 'book']),
            models.Index(fields=['is_active']),
            models.Index(fields=['start_date']),
            models.Index(fields=['end_date'])
        ]

    def __str__(self):
        return f"{self.club.name} - {self.book.title} ({self.start_date} to {self.end_date})"

class ScheduleMilestone(models.Model):
    """
    Schedule Milestone Table
    
    Defines specific milestones/checkpoints in a reading schedule.
    
    Variables:
        schedule: Foreign Key to ReadingSchedule
        title: Title of the milestone 
        target_date: When this milestone should be completed by
        page_start: Starting page for this milestone
        page_end: Ending page for this milestone
        description: Optional description with more details
    """
    schedule = models.ForeignKey(
        "ReadingSchedule", 
        on_delete=models.CASCADE, 
        related_name="milestones"
    )
    title = models.CharField(max_length=100)
    target_date = models.DateField()
    page_start = models.PositiveIntegerField(null=True, blank=True)
    page_end = models.PositiveIntegerField(null=True, blank=True)
    chapter_start = models.CharField(max_length=50, null=True, blank=True)
    chapter_end = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Schedule Milestone"
        verbose_name_plural = "Schedule Milestones"
        ordering = ['schedule', 'target_date']
        indexes = [
            models.Index(fields=['schedule']),
            models.Index(fields=['target_date'])
        ]

    def __str__(self):
        return f"{self.schedule.club.name} - {self.title} ({self.target_date})"


    
# Post table for book club post and community post.
class Post(models.Model):
    """
    Post Model

    Variables:
        user: ForiegnKey to User table (author of the post)
        thumbnail: up to 255 character string that represents the title of post.
        content: Text content of the post
        created_on: Date that the post was created.
        page_num: Optional integer represents the page number that the post is relevant to (or up to).
        flagged_count: Integer, default 0, number of times the post has been flagged for violating TOS.
        like_count: Integer, defualt 0, number of times the post has been liked.

        community: ForiegnKey refrencing comnmunity table.
        club: ForiegnKey refrencing the book club table.

    Functions:
        clean: Ensures data entry not filled with both or neither of the foriegn key types.

    Classes:
        Meta: Serves constaints to ensure data integrity.
    """

    # Should have one and only one of these relations.
    community = models.ForeignKey(
        "Community", 
        on_delete=models.CASCADE, 
        related_name="community_posts", 
        null = True, 
        blank = True
        )
    club = models.ForeignKey(
        "BookClub", 
        on_delete=models.CASCADE, 
        related_name="club_posts", 
        null = True, 
        blank = True
        )
    user = models.ForeignKey(
        "User", 
        on_delete=models.CASCADE, 
        related_name="user_posts"
        )
    title = models.CharField(max_length=250) 
    content = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    flagged_count = models.PositiveIntegerField(default = 0)
    like_count = models.PositiveIntegerField(default = 0)
    page_num = models.PositiveIntegerField(null = True, blank = True)
    
    # Stops bad data from being saved by Djano ORM.
    def clean(self):
        """
        Ensure a post is linked exactly one of (BookClub or Community)
        """
        if self.club and self.community:
            raise ValidationError("A post cannot belong to both a BookClub and a Community.")
        if not self.club and not self.community:
            raise ValidationError("A post must belong to either a BookClub or a Community.")
        super().clean()
    
    def save(self, *args, **kwargs):
        """
        Run validation before saving the post.
        """
        self.full_clean()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Post by {self.user} in {'BookClub' if self.club else 'Community'}"
    
    # Stops bad data from existing in the database (if somehow Django ORM clean is bypassed).
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=(
                    (models.Q(club__isnull=False) & models.Q(community__isnull=True)) |
                    (models.Q(club__isnull=True) & models.Q(community__isnull=False))
                ),
                name="post_must_have_one_relation"
            )
        ]
        verbose_name = "Post"
        verbose_name_plural = "Posts"
        indexes = [
            models.Index(fields=["title"]),
            models.Index(fields=["like_count"]),
            models.Index(fields=["page_num"])
        ]
        ordering = ["-created_on"]

# Comment base class and concrete class for comments.
# We use the Abstract Base Class method to deal with the polymorphism issue of our many comment types.
# To add a new comment type simply add a new concrete class.
# Base comment class:
class BaseComment(MPTTModel):
    """
    Abstract Base Class for Comments.

    Variables:
        user: FK to User table (author of the comment)
        content: Text content of the comment
        created_on: DateTime when the comment was created.
        flagged_count: Number of times the comment was flagged as violating TOS.
        like_count: Number of times the comment was liked.
        page_num: Optional page number refrence.
        parent: TreeForiegnKey using MPTT, whcih allows for deeply nested comments stored in tree structure.
    """

    user = models.ForeignKey(
        "User",
        on_delete=models.CASCADE,
        related_name="%(class)s_comments" 
    )
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    flagged_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    page_num = models.PositiveIntegerField(null=True, blank=True)
    parent = TreeForeignKey(
        'self',
        on_delete = models.SET_NULL,
        null = True,
        blank = True,
        related_name = "children"
    )
    

    class Meta:
        abstract = True
        ordering = ['-created_on']
        indexes = [
            models.Index(fields=["like_count"]),
            models.Index(fields=["page_num"]),
            models.Index(fields=["created_on"])
        ]
    
    # Tree insertion order specification.
    class MPTTMeta:
        order_insertion_by = ['-created_on']
    
    def __str__(self):
        return f"Comment by {self.user} - {self.content[:20]}"
    
# Concrete Classes
class PostComment(BaseComment):
    """
    Concrete Comment Model for Post Comments
    """
    post = models.ForeignKey("Post", on_delete=models.CASCADE, related_name="comments")

class ReviewComment(BaseComment):
    """
    Concrete Comment Model for Review Comments
    """
    review = models.ForeignKey("Review", on_delete=models.CASCADE, related_name="comments")

class ShelfComment(BaseComment):
    """
    Concrete Comment Model for Shelf Comments
    """
    shelf = models.ForeignKey("Shelf", on_delete=models.CASCADE, related_name="comments")

# Do you see this