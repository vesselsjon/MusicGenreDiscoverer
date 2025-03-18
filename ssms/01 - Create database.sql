/*
CREATE DATABASE [MusicGenreDiscoverer];
GO
*/

USE [MusicGenreDiscoverer];
GO

DROP TABLE IF EXISTS [MusicGenreDiscoverer].[dbo].[Songs];
GO

CREATE TABLE [MusicGenreDiscoverer].[dbo].[Songs] (
    [Id] INT PRIMARY KEY IDENTITY(1,1),         -- Auto-incrementing ID for each song
    [Name] NVARCHAR(255) NOT NULL,          -- Song name (e.g., "Shape of You")
    [Artist] NVARCHAR(255) NOT NULL,             -- Artist name (e.g., "Ed Sheeran")
    [Genre] NVARCHAR(50),                        -- Genre of the song (e.g., "Pop")
    [Features] VARBINARY(MAX),                   -- Serialized feature vector (e.g., embeddings)
    [DateAdded] DATETIME DEFAULT GetDate()      -- Date when the song was added to the database
);
GO
