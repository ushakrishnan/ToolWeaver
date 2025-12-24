"""Test connection and run GitHub operations example"""

if __name__ == "__main__":
    # Import the github_ops module which contains the main demo
    import asyncio
    from github_ops import main
    
    # Run the async main function
    asyncio.run(main())
