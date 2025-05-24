MERGE INTO [UsrUseMeLikeYouWant167] AS Target
    USING (select Id, CreatedOn, CreatedById, ModifiedOn,ModifiedById, Name, Description, City, TypeId from UsrAllDomainUsers where TypeId IN ('95F09DDC-1060-457A-B3D7-0419AA35B8D3','9162C5C1-12F3-443A-9D2A-D777EF3D1564','C35EDEF7-7FF2-4966-AFBE-9EFC2985C75D')) as Source
        ON Source.Name = Target.Name

    WHEN NOT MATCHED BY SOURCE
    THEN DELETE
        
    WHEN NOT MATCHED BY TARGET
    THEN INSERT (Id, CreatedOn, CreatedById, ModifiedOn,ModifiedById, Name, Description, City, TypeId) 
	VALUES (Source.Id, Source.CreatedOn, Source.CreatedById, Source.ModifiedOn,Source.ModifiedById, Source.Name, Source.Description, Source.City, Source.TypeId);